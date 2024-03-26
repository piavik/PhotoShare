from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
from cloudinary.uploader import destroy
from typing import Optional, List

from app.src.schemas import (
    PhotoResponse,
    PhotoModel,
    PhotoDb,
    PhotoDetailedResponse,
    TagModel,
)
from app.src.database.db import get_db
from app.src.database.models import User, Photo
from app.src.repository import photos as repository_photos
from app.src.services.auth import auth_service, RoleChecker
from app.src.conf.config import settings

router = APIRouter(prefix="/photos", tags=["photos"])

cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


@router.post(
    "/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED
)
async def create_photo(
    file: UploadFile = File(...),
    description: str = Form(...),
    tags: str = Form(""),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    tags_list = tags.split(",")
    file.file.seek(0)
    upload_result = cloudinary.uploader.upload(file.file)

    if not upload_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload photo",
        )

    if "secure_url" not in upload_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve secure URL for photo",
        )

    photo_create = PhotoModel(
        photo_url=upload_result["secure_url"],
        owner_id=current_user.id,
        description=description,
    )

    created_photo = await repository_photos.create_photo(
        db=db,
        photo_to_create=photo_create,
        user_id=current_user.id,
        tags_list=tags_list,
    )

    photo_response = PhotoResponse(
        photo=PhotoDb(
            id=created_photo.id,
            photo_url=created_photo.photo_url,
            owner_id=created_photo.owner_id,
            description=created_photo.description,
        ),
        detail="Photo successfully uploaded",
    )
    return photo_response


@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if photo.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=403, detail="Not enought rights to delete this photo"
            )

    public_id = photo.photo_url.split("/")[-1].split(".")[0]
    result = cloudinary.uploader.destroy(public_id=public_id, invalidate=True)

    print(result)

    db.delete(photo)
    db.commit()

    return {"detail": "Photo succesfuly deleted"}


@router.get("/{photo_id}", response_model=PhotoDetailedResponse)
async def read_photo(
    photo_id: int,
    db: Session = Depends(get_db),
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.put("/{photo_id}/tags", response_model=PhotoDetailedResponse)
async def update_photo_tags(
    photo_id: int,
    tags: str = Form(""),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not enough rights to edit tags of this photo"
        )

    updated_photo = await repository_photos.edit_photo_tags(
        db, photo_id, current_user.id, tags.split(",")
    )
    if not updated_photo:
        raise HTTPException(status_code=404, detail="Failed to update tags")

    updated_photo = PhotoDetailedResponse(
        id=updated_photo.id,
        photo_url=updated_photo.photo_url,
        owner_id=updated_photo.owner_id,
        description=updated_photo.description,
        tags=[TagModel(name=tag.name) for tag in updated_photo.tags],
        created_at=updated_photo.created_at,
        updated_at=updated_photo.updated_at,
    )

    return updated_photo


@router.put("/{photo_id}/description", response_model=PhotoResponse)
async def update_description(
    photo_id: int,
    description: str = Form(...),
    current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
    db: Session = Depends(get_db),
    ):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if  photo.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Not enough permissions to change the description"
        )

    try:
        updated_photo = await repository_photos.edit_photo_description(
            db, photo_id, photo.owner_id, description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PhotoResponse(
        photo=PhotoDb(
            id=photo.id,
            photo_url=photo.photo_url,
            owner_id=photo.owner_id,
            description=updated_photo.description,
        ),
        detail="Description successfully updated",
    )
