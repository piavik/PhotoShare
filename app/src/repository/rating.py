from sqlalchemy.orm import Session
from sqlalchemy import func
from app.src.schemas import RateDb
from app.src.database.models import User, Photo, Rate


async def rate_photo(db: Session, user_id: int, photo_id: int, rate: int):
    """
    rate_photo
    Adds a new rating for a photo in the database and updates the photo's average rating.
    Args:
        db (Session): database
        user_id (int): current session user id
        photo_id (int): id of the photo to be rated
        rate (int): rate from the current user

    Returns:
        Rate or None: The new Rate object if the rating was added successfully, 
        None if the user has already rated this photo.
    """

    existing_rate = (
        db.query(Rate)
        .join(Photo, Rate.photo_id == Photo.id)
        .join(User, Rate.user_id == User.id)
        .filter(Rate.photo_id == photo_id, Rate.user_id == user_id)
        .first()
    )
    if existing_rate:
        return None

    new_rate = Rate(rate=rate, photo_id = photo_id, user_id = user_id)

    db.add(new_rate)
    db.commit()

    average_rating = db.query(func.avg(Rate.rate)).filter_by(photo_id=photo_id).scalar()

    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    photo.rating = average_rating
    db.commit()

    return new_rate


async def get_rates(photo_id: int, db: Session):
    """
    Returns rates for particular photo

    Args:
        photo_id (int): ID of the photo
        db (Session): database session

    Returns:
        List[Rate]: list of the rates given to the photo
    """

    rates = db.query(Rate).filter(Rate.photo_id == photo_id).all()

    if not rates:
        return False

    return rates


async def delete_rate(rate_id: int, db: Session):
    """
    Delete rate from the database and recalculates photo's average rating.

    Args:
        rate_id (int): ID of the rate
        db (Session): database session

    Returns:
        bool: result
    """
    rate = (
        db.query(Rate)
        .filter(Rate.id == rate_id)
        .first()
    )

    if not rate:
        return False

    photo_id = rate.photo_id

    db.delete(rate)
    db.commit()

    average_rating = db.query(func.avg(Rate.rate)).filter_by(photo_id=photo_id).scalar()

    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not average_rating:
        photo.rating = 0.0
        db.commit()

    photo.rating = average_rating
    db.commit()

    return True
