import cloudinary.uploader
from typing import Optional
from app.src.conf.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


async def upload_photo(file):
    return cloudinary.uploader.upload(file)


async def delete_photo(cloudinary_url: str):
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
