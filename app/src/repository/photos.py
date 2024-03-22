from sqlalchemy.orm import Session

from app.src.database.models import Photo, Tag
from app.src.schemas import PhotoModel, PhotoDb

from cloudinary.uploader import upload


async def create_photo(db: Session, photo_to_create: PhotoModel, user_id: int, tags_list: list[str]):

    new_photo = Photo(**photo_to_create.dict())

    for tag_name in tags_list:
        tag = db.query(Tag).filter(Tag.name == tag_name.strip()).first()
        if not tag: 
            tag = Tag(name=tag_name.strip())
            db.add(tag)
            db.commit()

        new_photo.tags.append(tag)
    
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    db.commit()
    return new_photo
