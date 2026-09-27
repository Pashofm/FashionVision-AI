import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional

from backend.app.config import settings


def configure_cloudinary():
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )


def upload_image(
    file_path: str = None,
    file: bytes = None,
    public_id: Optional[str] = None,
    folder: str = "fashionvision/products",
    resource_type: str = "image"
) -> dict:
    configure_cloudinary()

    if file_path:
        result = cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            folder=folder,
            resource_type=resource_type,
            overwrite=True,
            unique_filename=False
        )
    elif file:
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder=folder,
            resource_type=resource_type,
            overwrite=True,
            unique_filename=False
        )
    else:
        raise ValueError("Either file_path or file must be provided")

    return {
        "public_id": result.get("public_id"),
        "url": result.get("secure_url"),
        "secure_url": result.get("secure_url"),
        "original_filename": result.get("original_filename"),
        "format": result.get("format"),
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes")
    }


def delete_image(public_id: str, resource_type: str = "image") -> dict:
    configure_cloudinary()

    result = cloudinary.uploader.destroy(
        public_id,
        resource_type=resource_type
    )

    return {"result": result}


def get_image_info(public_id: str, resource_type: str = "image") -> dict:
    configure_cloudinary()

    result = cloudinary.api.resource(
        public_id,
        resource_type=resource_type
    )

    return {
        "public_id": result.get("public_id"),
        "url": result.get("secure_url"),
        "width": result.get("width"),
        "height": result.get("height"),
        "format": result.get("format")
    }
