from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.src.database.models import Photo, Tag
from app.src.schemas import PhotoModel, PhotoDb, TagModel

from cloudinary.uploader import upload


async def create_photo(db: Session, photo_to_create: PhotoModel, user_id: int, tags_list: list[str]):

    new_photo = Photo(**photo_to_create.dict())

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

    for tag in valid_tags:
        new_photo.tags.append(tag)
    
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    db.commit()
    return new_photo
