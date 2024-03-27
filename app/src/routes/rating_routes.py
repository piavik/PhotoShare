from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.src.database import SessionLocal
from app.src.services.rating_service import RatingService

router = APIRouter()


@router.post("/photos/{photo_id}/rate", status_code=201)
def rate_photo(
    photo_id: int, rating: int, user_id: int, db: Session = Depends(SessionLocal)
):
    rating_service = RatingService(db)
    rating_service.rate_photo(user_id=user_id, photo_id=photo_id, rating=rating)
    return {"message": "Photo rated successfully"}
