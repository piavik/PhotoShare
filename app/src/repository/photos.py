from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import ValidationError

from app.src.database.models import Photo, Tag
from app.src.schemas import PhotoModel, TagModel


async def create_photo(db: Session, photo_to_create: PhotoModel, user_id: int, tags_list: list[str]):

    new_photo = Photo(**photo_to_create.model_dump())

    valid_tags = process_tags(db, tags_list)
    for tag in valid_tags:
        new_photo.tags.append(tag)

    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    return new_photo


async def get_photo_by_id(db: Session, photo_id: int):
    return db.query(Photo).filter(Photo.id == photo_id).first()


async def edit_photo_tags(
    db: Session, photo_id: int, user_id: int, new_tags: str
):
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.owner_id == user_id).first()

    if not photo:
        return None

    tags_list = [tag for tag in new_tags.strip().split(" ") if tag]

    new_tags = process_tags(db, tags_list)

    if not new_tags:
        return None
     
    photo.tags.clear()
    photo.tags = new_tags

    db.commit()
    return photo


def process_tags(db: Session, tags_list: list[str]):
    
    valid_tags = []
    for tag_name in tags_list:
        try:
            tag_data = TagModel(name=tag_name)
            tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
            if not tag:
                tag = Tag(name=tag_data.name)
                db.add(tag)
                db.commit()
            valid_tags.append(tag)
        except ValidationError as e:
            print(f"Tag validation error for '{tag_name}':", e.errors())
            continue

    return valid_tags[:5]


async def edit_photo_description(db: Session, photo_id: int, user_id: int, new_description: str):
    photo = (
        db.query(Photo).filter(Photo.id == photo_id, Photo.owner_id == user_id).first()
    )
    if not photo:
        return None

    if photo.description and not new_description.strip():
        raise ValueError("Cannot remove existing description")

    photo.description = new_description
    db.commit()
    return photo


async def delete_photo(db: Session, photo_id: int, user_id: int):
    photo = (
        db.query(Photo).filter(Photo.id == photo_id, Photo.owner_id == user_id).first()
    )
    if not photo:
        return None
    db.delete(photo)
    db.commit()
    return True


async def find_photos(db: Session, 
                      key_word: Optional[str] = None,
                      sort_by: Optional[str] = None,
                      min_rating: Optional[float] = None,
                      max_rating: Optional[float] = None,
                      start_date: Optional[date] = None,
                      end_date: Optional[date] = None,
                      ):

    q = key_word.strip() if key_word else ""
    if not q:
        return []

    photos = db.query(Photo).filter(
            or_(
                Photo.description.ilike(f"%{q}%"),
                Photo.tags.any(Tag.name.ilike(f"%{q}%")),
            )
        )

    if min_rating is not None:
        photos = photos.filter(Photo.rating >= min_rating)

    if max_rating is not None:
        photos = photos.filter(Photo.rating <= max_rating)

    if start_date:
        photos = photos.filter(Photo.created_at >= start_date)

    if end_date:
        photos = photos.filter(Photo.created_at <= end_date)

    if sort_by == 'rating':
        photos = photos.order_by(Photo.rating.desc())
        
    elif sort_by == 'date':
        photos = photos.order_by(Photo.created_at.desc())

    return photos.all()
