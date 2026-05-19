from typing import Any, Dict, List, Optional
import os
import json
import requests

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

router = APIRouter(prefix="/leaf", tags=["leaf"])


class LeafDetectResponse(BaseModel):
    label: str
    confidence: Optional[float] = None
    matches: List[Dict[str, Any]] = []


def _azure_endpoint() -> str:
    return os.environ.get("AZUREML_ENDPOINT_URL", "https://plant-endpoint.centralindia.inference.ml.azure.com/score")


def _azure_key() -> str:
    key = os.environ.get("AZUREML_ENDPOINT_KEY")
    if not key:
        raise RuntimeError("AZUREML_ENDPOINT_KEY not set in environment")
    return key


def _call_azure(image_bytes: bytes) -> Dict:
    url = _azure_endpoint()
    key = _azure_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    # Endpoint expects array of byte values (per user snippet)
    payload = {"image": list(image_bytes)}

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Azure endpoint error: {exc} - {resp.text}")

    try:
        return resp.json()
    except Exception:
        raise RuntimeError("Azure response is not valid JSON")


def _parse_label(resp_json: Dict) -> Dict[str, Optional[float]]:
    # Common patterns: {'label': 'X', 'confidence': 0.9}, or {'predictions':[{'label':..., 'confidence':...}]}
    if not isinstance(resp_json, dict):
        return {"label": str(resp_json), "confidence": None}

    # direct keys
    for key in ("label", "class", "prediction", "predicted_label"):
        if key in resp_json:
            return {"label": str(resp_json[key]), "confidence": float(resp_json.get("confidence", None)) if resp_json.get("confidence") is not None else None}

    preds = resp_json.get("predictions") or resp_json.get("results")
    if isinstance(preds, list) and preds:
        first = preds[0]
        if isinstance(first, dict):
            for k in ("label", "class", "prediction", "predicted_label"):
                if k in first:
                    return {"label": str(first[k]), "confidence": float(first.get("confidence", None)) if first.get("confidence") is not None else None}
            # fallback: if first has 'scores' or similar
            if "score" in first:
                return {"label": str(first.get("score")), "confidence": None}

    # Try keys at top-level with single key
    if len(resp_json) == 1:
        val = next(iter(resp_json.values()))
        return {"label": str(val), "confidence": None}

    return {"label": "unknown", "confidence": None}


def _load_dataset() -> Dict[str, Any]:
    base = Path(__file__).resolve().parents[2]
    ds_path = base / "app" / "dataset" / "village_plant_disease_dataset.json"
    if not ds_path.exists():
        raise RuntimeError("Dataset file not found: village_plant_disease_dataset.json")
    with ds_path.open("r", encoding="utf-8") as f:
        return json.load(f)


from pathlib import Path


@router.post("/detect", response_model=LeafDetectResponse)
def detect_leaf(image: UploadFile = File(...)):
    try:
        content = image.file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    try:
        resp_json = _call_azure(content)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    parsed = _parse_label(resp_json)
    label = parsed.get("label") or "unknown"
    confidence = parsed.get("confidence")

    # load dataset and try to find matches
    matches: List[Dict[str, Any]] = []
    try:
        ds = _load_dataset()
        if isinstance(ds, list):
            for rec in ds:
                # match against common fields
                for field in ("disease", "name", "label", "plant", "crop"):
                    if isinstance(rec, dict) and field in rec and isinstance(rec[field], str):
                        if label.lower() in rec[field].lower() or rec[field].lower() in label.lower():
                            matches.append(rec)
                            break
        elif isinstance(ds, dict):
            # if dict of entries, include those whose string content matches
            for k, rec in ds.items():
                if isinstance(rec, dict):
                    text = json.dumps(rec)
                    if label.lower() in text.lower():
                        matches.append(rec)
    except Exception:
        # non-fatal: ignore dataset loading issues
        matches = []

    return LeafDetectResponse(label=label, confidence=confidence, matches=matches)
