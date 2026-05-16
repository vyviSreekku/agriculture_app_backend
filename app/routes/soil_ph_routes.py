from fastapi import APIRouter, UploadFile, File, HTTPException
import random

router = APIRouter(prefix="/soil-ph", tags=["soil-ph"])


@router.post("/analyze")
async def analyze_soil_ph(image: UploadFile = File(...)):
	"""Analyze soil pH from an uploaded image.

	Note: This endpoint currently returns a simulated value.
	"""

	if not image.content_type or not image.content_type.startswith("image/"):
		raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

	await image.read()  # simulate processing
	ph_value = round(random.uniform(4.0, 9.0), 1)
	return {"ph_value": ph_value}
