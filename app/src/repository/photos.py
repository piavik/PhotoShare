from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import ValidationError

from app.src.database.models import Photo, Tag
from app.src.schemas import PhotoModel, TagModel


async def create_photo(db: Session, photo_to_create: PhotoModel, user_id: int, tags_list: list[str]) -> Photo:
    """
    **Create photo endpoint**

    Args:
        db (Session): [description]
        photo_to_create (PhotoModel): [description]
        user_id (int): [description]
        tags_list (list[str]): [description]

    Returns:
        [Photo]: [description]
    """
    new_photo = Photo(**photo_to_create.model_dump())

    valid_tags = process_tags(db, tags_list)
    for tag in valid_tags:
        new_photo.tags.append(tag)

    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    return new_photo


async def get_photo_by_id(db: Session, photo_id: int):
    """
    **Get photo by it's ID**

    Args:
        db (Session): [description]
        photo_id (int): [description]

    Returns:
        [Photo]: [description]
    """    
    return db.query(Photo).filter(Photo.id == photo_id).first()


async def edit_photo_tags(db: Session, photo_id: int, new_tags: str) -> Photo | None:
    """
    **Edit tag of the photo**

    Args:
        db (Session): [description]
        photo_id (int): [description]
        new_tags (str): [description]

    Returns:
        [Photo] or None: [description]
    """
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

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


def process_tags(db: Session, tags_list: list[str]) -> list:
    """
    **Inner function for tags validation**

    Args:
        db (Session): [description]
        tags_list (list[str]): [description]

    Returns:
        [list]: [description]
    """    
    valid_tags = []
    unique_tags_name = set()
    for tag_name in tags_list:
        if tag_name in unique_tags_name:
            continue
        try:
            tag_data = TagModel(name=tag_name)
            tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
            if not tag:
                tag = Tag(name=tag_data.name)
                db.add(tag)
                db.commit()
            unique_tags_name.add(tag_name)
            valid_tags.append(tag)

        except ValidationError as e:
            print(f"Tag validation error for '{tag_name}':", e.errors())
            continue

    return valid_tags[:5]


async def edit_photo_description(db: Session, photo_id: int, user_id: int, new_description: str) -> Photo:
    """
    **Edit description of the photo**

    Args:
        db (Session): [description]
        photo_id (int): [description]
        user_id (int): [description]
        new_description (str): [description]

    Raises:
        ValueError: [description]

    Returns:
        [Photo]: [description]
    """    
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


async def delete_photo(db: Session, photo_id: int, user_id: int) -> bool:
    """
    **Delete photo**

    Args:
        db (Session): [description]
        photo_id (int): [description]
        user_id (int): [description]

    Returns:
        [bool]: [description]
    """    
    photo = (
        db.query(Photo).filter(Photo.id == photo_id, Photo.owner_id == user_id).first()
    )
    if not photo:
        return False
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
    """
    **Search photo by given criteria**

    Args:
        db (Session): [description]
        key_word (Optional[str], optional): [description]. Defaults to None.
        sort_by (Optional[str], optional): [description]. Defaults to None.
        min_rating (Optional[float], optional): [description]. Defaults to None.
        max_rating (Optional[float], optional): [description]. Defaults to None.
        start_date (Optional[date], optional): [description]. Defaults to None.
        end_date (Optional[date], optional): [description]. Defaults to None.

    Returns:
        [list]: [description]
    """
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
