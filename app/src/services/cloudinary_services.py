import cloudinary.uploader
from typing import Optional

from fastapi import HTTPException, status
from app.src.conf.config import settings, cloudinary_config


async def upload_photo(file):
    """upload_photo
    Uploads photo onto cloudinary server
    Args:
        file ([file]): photo to be upload on cloudinary
    Raises:
        HTTPException: provided file has pother than allowed_formats format
    """
    try:
        upload_result = cloudinary.uploader.upload(
            file, 
            allowed_formats=["jpg", "jpeg", "png", "webp", "bmp", "gif", "svg", "tif", "tiff"]
        )
    except cloudinary.exceptions.Error as e:
        print(f"Error uploading to Cloudinary: {e}")
        raise HTTPException(status_code=400, detail="Error uploading image.")


async def delete_photo(cloudinary_url: str):
    """delete_photo
    Deletes photo from the cloudinary server 
    Args:
        cloudinary_url (str): photo's url on cloudinary

    Returns:
        [dict]: A dictionary containing the result of the deletion operation.
    """
    public_id = cloudinary_url.split("/")[-1].split(".")[0]
    return cloudinary.uploader.destroy(public_id, invalidate=True) 


async def transformed_photo_url(
        photo_url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: Optional[str] = None,
        angle: Optional[int] = None,
        filter: Optional[str] = None,
        gravity: Optional[str] = None,
    ):
    """
    transformed_photo_url
    Applies provided transformation parameters and return url to transformed photo
    Args:
        photo_url (str): photo's url on cloudinary
        width (Optional[int], optional): new width. Defaults to None.
        height (Optional[int], optional): new height. Defaults to None.
        crop (Optional[str], optional): cropping options. Defaults to None.
        angle (Optional[int], optional): new angle. Defaults to None.
        filter (Optional[str], optional): filter to be applied. Defaults to None.
        gravity (Optional[str], optional): gravity to be applied. Defaults to None.

    Returns:
        [str]: transformed photo's url on cloudinary
    """
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

    if not transformations:
        return None

    transformation_string = ",".join(transformations)
    public_id = photo_url.split("/")[-1].split(".")[0]
    new_url = ""

    if transformation_string:
        new_url = f"https://res.cloudinary.com/{cloudinary.config().cloud_name}/image/upload/{transformation_string}/{public_id}.jpg"

    return new_url
