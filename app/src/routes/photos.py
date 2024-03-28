from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
from cloudinary.uploader import destroy
from typing import Optional, List
import qrcode
from io import BytesIO

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
    tags_list = tags.strip().split(" ")
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

    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enought rights to delete this photo"
            )

    public_id = photo.photo_url.split("/")[-1].split(".")[0]
    result = cloudinary.uploader.destroy(public_id=public_id, invalidate=True)

    await repository_photos.delete_photo(db, photo_id, photo.owner_id)

    return {"detail": "Photo succesfuly deleted"}


@router.get("/find_photos", response_model=list[PhotoDetailedResponse])
async def get_photos_by_key_word(
    key_word: str = "",
    db: Session = Depends(get_db),
):
    if not key_word.strip():
        raise HTTPException(status_code=404, detail="No key word provided")
    photos = await repository_photos.find_photos(db, key_word)
    if not photos:
        raise HTTPException(status_code=404, detail=f"No photos found by key word '{key_word}'")
    return photos


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
    tags: str = Form("", description="Print your tags separated with space"),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough rights to edit tags of this photo"
            )

    if not tags.strip().split():
        raise HTTPException(
            status_code=400,
            detail="No valid tags provided, existing tags remain unchanged",
        )

    updated_photo = await repository_photos.edit_photo_tags(db, photo_id, current_user.id, tags)

    if not updated_photo:
        raise HTTPException(status_code=404, detail="Failed to update tags")

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
    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not enough rights to change the description to this photo",
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


@router.post("/{photo_id}/transform", response_model=PhotoDetailedResponse)
async def transform_photo(
    photo_id: int,
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    crop: Optional[str] = Form(
        None, description="Type of crop (scale, fill, fit, etc.)"
    ),
    angle: Optional[int] = Form(None),
    filter: Optional[str] = Form(
        None, description="Apply a filter (sepia, grayscale, etc.)"
    ),
    gravity: Optional[str] = Form(
        None, description="Gravity for cropping (north, south, east, west, face, etc.)"
    ),
    current_user: User = Depends(RoleChecker(["user"])),
    db: Session = Depends(get_db),
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enought rights to transform this photo"
            )

    transformations = []
    if width:
        transformations.append(f"w_{width}")
    if height:
        transformations.append(f"h_{height}")
    if crop:
        transformations.append(f"c_{crop}")
    if angle:
        transformations.append(f"a_{angle}")
    if filter:
        transformations.append(f"e_{filter}")
    if gravity:
        transformations.append(f"g_{gravity}")

    transformation_string = ",".join(transformations)
    if transformation_string:
        public_id = photo.photo_url.split("/")[-1].split(".")[0]
        new_url = f"https://res.cloudinary.com/{cloudinary.config().cloud_name}/image/upload/{transformation_string}/{public_id}.jpg"
        photo.changed_photo_url = new_url

        transformed_photo = await repository_photos.create_photo(
            db,
            PhotoModel(
                photo_url=new_url,
                owner_id=current_user.id,
                description=f"This is a transformed version of photo id {photo_id}",
            ),
            user_id=current_user.id,
            tags_list=[],
        )
    else:
        raise HTTPException(status_code=400, detail="No transformations provided")

    photo = await repository_photos.get_photo_by_id(db, photo_id)
    transformed_photo_url = photo.changed_photo_url

    if not transformed_photo_url:
        raise HTTPException(status_code=404, detail="Transformed photo URL not found")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(transformed_photo_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_io = BytesIO()
    img.save(img_io, format="PNG")
    img_io.seek(0)

    return StreamingResponse(img_io, media_type="image/png")
