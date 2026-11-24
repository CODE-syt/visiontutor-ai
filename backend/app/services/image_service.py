"""Image intake pipeline: validate -> decode -> preprocess -> base64 for the AI service."""
from fastapi import UploadFile

from app.config import Settings
from app.utils.file_utils import bytes_to_pil, pil_to_base64_jpeg, preprocess_image
from app.utils.validators import validate_upload


async def prepare_image_for_analysis(file: UploadFile, settings: Settings) -> str:
    """Reads, validates, cleans, and base64-encodes an uploaded image.
    Returns a base64 JPEG string ready to hand to a vision-language model."""
    raw_bytes = await file.read()
    validate_upload(file, raw_bytes, settings.max_upload_mb)

    img = bytes_to_pil(raw_bytes)
    img = preprocess_image(img)
    return pil_to_base64_jpeg(img)
