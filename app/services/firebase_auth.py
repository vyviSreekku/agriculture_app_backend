import json
import os
from functools import lru_cache
from typing import Any, Dict


class FirebaseAuthError(RuntimeError):
    pass


def _get_service_account_info() -> Dict[str, Any]:
    """Load Firebase Admin credentials.

    Provide ONE of:
      - FIREBASE_SERVICE_ACCOUNT_JSON (full JSON string)
      - FIREBASE_SERVICE_ACCOUNT_FILE (path to JSON file)

    Never commit service account JSON into the repo.
    """

    raw_json = (os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or "").strip()
    if raw_json:
        try:
            info = json.loads(raw_json)
            if not isinstance(info, dict):
                raise FirebaseAuthError("FIREBASE_SERVICE_ACCOUNT_JSON must be a JSON object")

            # A Firebase Admin service account JSON contains these keys.
            required_keys = {"type", "project_id", "private_key", "client_email"}
            if not required_keys.issubset(set(info.keys())):
                # Common mistake: putting Firebase Web config (apiKey/authDomain/...) here.
                if "apiKey" in info or "authDomain" in info:
                    raise FirebaseAuthError(
                        "FIREBASE_SERVICE_ACCOUNT_JSON appears to be Firebase *web* config (apiKey/authDomain/...). "
                        "Backend must use a Firebase Admin service account JSON (includes client_email and private_key)."
                    )

                missing = sorted(required_keys - set(info.keys()))
                raise FirebaseAuthError(
                    f"FIREBASE_SERVICE_ACCOUNT_JSON is missing required service-account keys: {missing}. "
                    "Use Firebase Console > Project settings > Service accounts > Generate new private key."
                )

            return info
        except json.JSONDecodeError as exc:
            raise FirebaseAuthError(
                "Invalid FIREBASE_SERVICE_ACCOUNT_JSON (must be valid JSON). "
                "Do not paste the Firebase Web config here; paste the Admin service account JSON."
            ) from exc

    file_path = (
        os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")
        or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        or ""
    ).strip()
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except OSError as exc:
            raise FirebaseAuthError(f"Failed reading FIREBASE_SERVICE_ACCOUNT_FILE: {exc}")

    raise FirebaseAuthError(
        "Firebase Admin not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_FILE."
    )


@lru_cache(maxsize=1)
def _get_firebase_app():
    """Initialize Firebase Admin app once (lazy)."""

    try:
        import firebase_admin
        from firebase_admin import credentials
    except Exception as exc:
        raise FirebaseAuthError(f"firebase-admin not installed/available: {exc}")

    if firebase_admin._apps:
        # Reuse if already initialized elsewhere
        return firebase_admin.get_app()

    cred = credentials.Certificate(_get_service_account_info())
    return firebase_admin.initialize_app(cred)


def verify_firebase_id_token(id_token: str) -> Dict[str, Any]:
    """Verify a Firebase ID token and return its decoded claims."""

    if not id_token or not id_token.strip():
        raise FirebaseAuthError("Missing Firebase ID token")

    _get_firebase_app()

    try:
        from firebase_admin import auth

        # Audience/project checks are handled via the service account project.
        decoded = auth.verify_id_token(id_token.strip(), check_revoked=False)
        if not isinstance(decoded, dict):
            raise FirebaseAuthError("Invalid decoded token")
        return decoded
    except Exception as exc:
        raise FirebaseAuthError(f"Invalid Firebase ID token: {exc}")


def get_verified_phone_from_claims(claims: Dict[str, Any]) -> str:
    phone = (claims.get("phone_number") or "").strip()
    if not phone:
        raise FirebaseAuthError("Token missing phone_number (did you sign in with Phone Auth?)")
    return phone
