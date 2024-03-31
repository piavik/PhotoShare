from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import ValidationError

from app.src.database.models import Photo, Tag
from app.src.schemas import PhotoModel, TagModel


async def create_photo(db: Session, photo_to_create: PhotoModel, user_id: int, tags_list: list[str]):
    """
    create_photo
    A function to create new photo record in database
    Args:
        db (Session): database
        photo_to_create (PhotoModel): object to create schema
        user_id (int): current session user id
        tags_list (list[str]): list of tags to be added to photo

    Returns:
        [ResponseType]: PhotoModel
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
    get_photo_by_id
    A function to find photo in database by photo's id
    Args:
        db (Session): database
        photo_id (int): photo to be returned

    Returns:
        Photo or None: The photo object if found, otherwise `None`
    """
    return db.query(Photo).filter(Photo.id == photo_id).first()


async def edit_photo_tags(db: Session, photo_id: int, new_tags: str):
    """
    edit_photo_tags
    A function to edit existing photo's tags
    Args:
        db (Session): database
        photo_id (int): id of the photo to be addited
        new_tags (str): string with new tags space separated

    Returns:
        Photo or None: The photo object if succesfuly eddited, 
        `None` if photo not found or new tags string include non 
        of valid tags
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
    process_tags
    A function to check if provided tags exisit in database and return a list of valid tags
    Args:
        db (Session): database
        tags_list (list[str]): list of strings to be added as tags to photo

    Returns:
        list[Tag]: A list of valid Tag model instances representing the processed tags,
                   limited to the first 5 unique valid tags found or created.
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


async def edit_photo_description(db: Session, photo_id: int, user_id: int, new_description: str):
    """
    edit_photo_description
    A function to edit current discription to photo.
    Args:
        db (Session): database
        photo_id (int): id of the photo description of which to be edited
        user_id (int): current session user id
        new_description (str): new description to be added to the photo

    Raises:
        ValueError: user try to delete existing description wo adding new

    Returns:
        Photo or None: The photo object if found, otherwise `None`
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


async def delete_photo(db: Session, photo_id: int,):
    """
    delete_photo
    Deletes photo founded by provided id
    Args:
        db (Session): database
        photo_id (int): id of the photo to be deleted

    Returns:
        True or None: 'True' is succesfully deleted, 'None' if photo was not found by id
    """
    photo = (
        db.query(Photo).filter(Photo.id == photo_id).first()
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
    find_photos
    Searches for photos in the database that match specified filters. Photos can be filtered by
    a keyword present in their description or tags, a rating range, and/or a creation date range.
    Results can be sorted by rating or creation date in descending order

    Args:
        db (Session): database
        key_word (Optional[str], optional): key word to be used as filter for query. Defaults to None.
        sort_by (Optional[str], optional): sort option for query return value. Defaults to None.
        min_rating (Optional[float], optional): minimal photo rating to be used as filter to query. Defaults to None.
        max_rating (Optional[float], optional): maximal photo rating to be used as filter to query. Defaults to None.
        start_date (Optional[date], optional): minimal photo creation date to be used as filter to query. Defaults to None.
        end_date (Optional[date], optional): maximal photo creation date to be used as filter to query. Defaults to None.

    Returns:
        List[Photo]: A list of Photo objects that match the criteria. Returns an empty list if no keyword is provided or no photos match the criteria.
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
