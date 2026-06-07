import cv2
import numpy as np
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from app.services.auth import get_optional_user
from app.services.claims import create_claim
from app.services.cost import estimate_repair_cost
from app.services.damage_detection import detect_damage_and_annotate
from app.services.preprocessing import preprocess_for_damage_detection
from app.utils.image_utils import encode_image_to_base64

router = APIRouter()


@router.post("/predict")
async def predict_damage(
    file: UploadFile = File(...),
    vehicle_segment: str = Form("sedan"),
    workshop_type: str = Form("standard"),
    car_model: str = Form("maruti_swift"),
    damage_category: str = Form("auto"),
    authorization: str | None = Header(default=None),
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Upload JPG, PNG, or WEBP.")

    image_bytes = await file.read()
    if len(image_bytes) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image is too large. Upload a file below 12 MB.")

    np_img = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Unable to read image.")

    try:
        processed_image, preprocessing_report = preprocess_for_damage_detection(image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = detect_damage_and_annotate(processed_image)
    estimate = estimate_repair_cost(
        detections=result["detections"],
        damage_area_ratio=result["damage_area_ratio"],
        vehicle_segment=vehicle_segment,
        workshop_type=workshop_type,
        car_model=car_model,
        damage_category=damage_category,
    )

    response = {
        "damage_detected": result["damage_detected"],
        "num_damages": result["num_damages"],
        "damage_types": result["damage_types"],
        "damage_area_ratio": result["damage_area_ratio"],
        "detections": result["detections"],
        "severity": estimate["severity"],
        "severity_score": estimate["severity_score"],
        "estimated_cost_range": estimate["estimated_cost_range"],
        "estimated_cost_min": estimate["estimated_cost_min"],
        "estimated_cost_max": estimate["estimated_cost_max"],
        "cost_breakdown": estimate,
        "preprocessing": preprocessing_report.as_dict(),
        "model": result["model"],
        "annotated_image": encode_image_to_base64(result["annotated_image"]),
    }

    user = get_optional_user(authorization)
    if user:
        claim = create_claim(user["id"], file.filename or "vehicle-image", response)
        response["claim"] = {
            "id": claim["id"],
            "claim_number": claim["claim_number"],
            "status": claim["status"],
            "created_at": claim["created_at"],
        }
    return response
