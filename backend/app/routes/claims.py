from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.auth import get_current_user
from app.services.claims import get_claim, list_claims, update_claim_status

router = APIRouter(prefix="/claims", tags=["claims"])


class StatusUpdate(BaseModel):
    status: str


@router.get("")
def claim_history(user: dict = Depends(get_current_user)):
    return {"claims": list_claims(user)}


@router.get("/{claim_id}")
def claim_detail(claim_id: int, user: dict = Depends(get_current_user)):
    claim = get_claim(user["id"], claim_id, allow_any=user["role"] == "admin")
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    return {"claim": claim}


@router.patch("/{claim_id}/status")
def change_claim_status(claim_id: int, payload: StatusUpdate, user: dict = Depends(get_current_user)):
    claim = update_claim_status(user, claim_id, payload.status)
    if not claim:
        raise HTTPException(status_code=403, detail="Only surveyors or admins can update claim status.")
    return {"claim": claim}
