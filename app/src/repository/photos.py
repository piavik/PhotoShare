from typing import List
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.src.database.models import Photo, Tag
from app.src.schemas import PhotoModel, TagModel


async def create_photo(db: Session, photo_to_create: PhotoModel, user_id: int, tags_list: list[str]):

    new_photo = Photo(**photo_to_create.dict())

    valid_tags = process_tags(db, tags_list)
    for tag in valid_tags:
        new_photo.tags.append(tag)

    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    db.commit()
    return new_photo


async def get_photo_by_id(db: Session, photo_id: int):
    return db.query(Photo).filter(Photo.id == photo_id).first()


async def edit_photo_tags(
    db: Session, photo_id: int, user_id: int, new_tags_list: List[str]
):
    photo = (
        db.query(Photo).filter(Photo.id == photo_id, Photo.owner_id == user_id).first()
    )
    if not photo:
        return None

    photo.tags.clear()
    new_tags = process_tags(db, new_tags_list)
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
