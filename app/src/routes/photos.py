from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Union
from datetime import date

from app.src.schemas import (
    PhotoResponse,
    PhotoModel,
    PhotoDb,
    PhotoDetailedResponse,
    SortOptions,
    ResponceOptions,
    UrlResponse,
    TagModel,
)
from app.src.database.db import get_db
from app.src.database.models import User, Photo
from app.src.repository import photos as repository_photos
from app.src.services.auth import auth_service, RoleChecker
from app.src.services.qr_code_service import generate_qr_code
from app.src.services import cloudinary_services
from app.src.conf.config import settings

router = APIRouter(prefix="/photos", tags=["photos"])

@router.post("/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_photo(
        file: UploadFile = File(...),
        description: str = Form(...),
        tags: str = Form(""),
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
    ):
    """
    **Create photo endpoint**
    Uploads photo into cloudinaty and create a new record in database.

    Args:
    - file (UploadFile, optional): File to upload
    - description (str, optional): File description
    - tags (str, optional): tags for the photo
    - current_user (User, optional): current user
    - db (Session, optional): database session.

    Raises:
    - HTTPException: 500 Failed to upload photo
    - HTTPException: 500 Failed to retrieve secure URL for photo

    Returns:
    - [PhotoResponse]: response object 
    """    
    tags_list = tags.strip().split(" ")
    file.file.seek(0)
    upload_result = await cloudinary_services.upload_photo(file.file) 

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
    ) -> dict:
    """
    **Delete photo endpoint**

    Args:
    - photo_id (int): ID of the photo
    - current_user (User, optional): current user
    - db (Session, optional): database session

    Raises:
    - HTTPException: 403 Not enought rights to delete this photo
    - HTTPException: 404 Photo not found

    Returns:
    - message: message
    """    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enought rights to delete this photo"
            )

    await cloudinary_services.delete_photo(photo.photo_url)
    await repository_photos.delete_photo(db, photo_id)

    return {"detail": "Photo succesfuly deleted"}


@router.get("/find_photos", response_model=list[PhotoDetailedResponse])
async def get_photos_by_key_word(
        db: Session = Depends(get_db),
        key_word: str = Query(None, description="Print key word"),
        sort_by: SortOptions = Query(None, description="Sort by 'raiting' or 'date'"),
        min_raiting: float = Query(None, description="Minimum rating filter"),
        max_rating: float = Query(None, description="Maximum rating filter"),
        start_date: date = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    ):
    """
    **Endpoint for photo searching**

    Args:
    - db (Session, optional): database session
    - key_word (str, optional): Keyword to search for. Defaults to None
    - sort_by (SortOptions, optional): Sort by 'raiting' or 'date'. Defaults to No sorting
    - min_raiting (float, optional): Minimum rating filter. Defaults to None
    - max_rating (float, optional): Maximum rating filter. Defaults to None
    - start_date (date, optional): Start date for filtering (YYYY-MM-DD). Defaults to None
    - end_date (date, optional): End date for filtering (YYYY-MM-DD). Defaults to None

    Raises:
    - HTTPException: 400 No key word provided
    - HTTPException: 404 No photos found by keyword

    Returns:
    - list[PhotoDetailedResponse]: detailed responce of the photo pbject
    """
    if not key_word:
        raise HTTPException(status_code=400, detail="No key word provided")

    photos = await repository_photos.find_photos(db, key_word, sort_by, min_raiting, max_rating, start_date, end_date)

    if not photos:
        raise HTTPException(status_code=404, detail=f"No photos found by key word '{key_word}'")
    return photos


@router.get("/{photo_id}", response_model=Union[PhotoDetailedResponse, UrlResponse])
async def read_photo(
        photo_id: int,
        db: Session = Depends(get_db),
        response_type: ResponceOptions = Query(default=ResponceOptions.detailed, description="Select a response option")
    ):
    """
    **Endpoint for getting photo by it's ID**
    Retrieves photo information by ID with various response formats based on user selection.

    Args:
    - photo_id (int): ID of the photo
    - db (Session, optional): database session.
    - response_type (ResponceOptions, optional): option for responce type. Defaults to detailed

    Raises:
    - HTTPException: 404 Photo not found

    Returns:
    - UrlResponse | StreamingResponse: either URL od QR code of the photo
    """
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if response_type == ResponceOptions.url:
        return UrlResponse(url=photo.photo_url)
    if response_type == ResponceOptions.qr_code:
        img_io = generate_qr_code(photo.photo_url)
        return StreamingResponse(img_io, media_type="image/png")
    return photo


@router.patch("/{photo_id}/tags", response_model=PhotoDetailedResponse)
async def update_photo_tags(
        photo_id: int,
        tags: str = Form("", description="Print your tags separated with space"),
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
    ):
    """
    **Endpoint for editing tags of the photo**
    Updates tags of the photo found by provided id, if valid new tags provided

    Args:
    - photo_id (int): ID of the photo
    - tags (str, optional): List of tags, separated by whitespace. Defaults to empty string
    - current_user (User, optional): current user
    - db (Session, optional): database session

    Raises:
    - HTTPException: 404 Photo not found
    - HTTPException: 403 Unsufficient permissions to edit tags of this photo
    - HTTPException: 400 No valid tags provided, existing tags remain unchanged
    - HTTPException: 400 Failed to update tags

    Returns:
    - [PhotoDetailedResponse]: detailed responce of the photo pbject
    """
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Unsufficient permissions to edit tags of this photo"
            )

    if not tags.strip().split():
        raise HTTPException(
            status_code=400,
            detail="No valid tags provided, existing tags remain unchanged",
        )

    updated_photo = await repository_photos.edit_photo_tags(db, photo_id, tags)

    if not updated_photo:
        raise HTTPException(status_code=400, detail="Failed to update tags")

    return updated_photo


@router.patch("/{photo_id}/description", response_model=PhotoResponse)
async def update_description(
        photo_id: int,
        description: str = Form(...),
        current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
        db: Session = Depends(get_db),
    ):
    """
    **Endpoint for updating the description of the photo**
    Updates description of the photo found by provided id, if valid new tags provided

    Args:
    - photo_id (int): ID of the photo
    - description (str, optional): Photo description
    - current_user (User, optional): current user
    - db (Session, optional): database session

    Raises:
    - HTTPException: 400 Bad request
    - HTTPException: 403 Unsufficient permissions to change the description to this photo
    - HTTPException: 404 Photo not found

    Returns:
    - [PhotoResponse]: responce of the photo pbject
    """    
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Unsufficient permissions to change the description to this photo",
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
    """
    **Photo transformation endpoint**
    Transforms photo using cloudinary transformation services, returning qr with transformed photo url
   

    Args:
    - photo_id (int): ID of the photo
    - width (Optional[int], optional): picture width. Defaults to None
    - height (Optional[int], optional): picture height. Defaults to None
    - crop (Optional[str], optional): Type of crop (scale, fill, fit, etc.). Defaults to None
    - angle (Optional[int], optional): rotation angle. Defaults to None
    - filter (Optional[str], optional): "Apply a filter (sepia, grayscale, etc.). Defaults to  None
    - gravity (Optional[str], optional): Gravity for cropping (north, south, east, west, face, etc.). Defaults to None
    - current_user (User, optional): current user
    - db (Session, optional): database session

    Raises:
    - HTTPException: 403 Unsufficient permissions to transform this photo
    - HTTPException: 400 No transformations provided
    - HTTPException: 404 Transformed photo URL not found

    Returns:
    - [PhotoDetailedResponse]: detailed responce of the photo pbject
    """
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if current_user.role != "admin":
        if photo.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Unsufficient permissions to transform this photo"
            )

    new_url = await cloudinary_services.transformed_photo_url(
        photo_url=photo.photo_url,
        width=width,
        height=height,
        crop=crop,
        angle=angle,
        filter=filter,
        gravity=gravity,
        )
    if not new_url:
        raise HTTPException(status_code=400, detail="No transformations provided")

    photo.changed_photo_url = new_url

    await repository_photos.create_photo(
            db,
            PhotoModel(
                photo_url=new_url,
                owner_id=current_user.id,
                description=f"This is a transformed version of photo id {photo_id}",
            ),
            user_id=current_user.id,
            tags_list=[],
        )

    photo = await repository_photos.get_photo_by_id(db, photo_id)
    transformed_photo_url = photo.changed_photo_url

    if not transformed_photo_url:
        raise HTTPException(status_code=404, detail="Transformed photo URL not found")

    img_io = generate_qr_code(transformed_photo_url)

    return StreamingResponse(img_io, media_type="image/png")
