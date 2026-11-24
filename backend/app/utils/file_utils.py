"""Safe temporary-file / in-memory image handling helpers."""
import base64
import io
from PIL import Image


def bytes_to_pil(raw_bytes: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.load()
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not decode image: {exc}") from exc
    return img


def preprocess_image(img: Image.Image, max_dimension: int = 1600) -> Image.Image:
    """Convert to RGB, strip metadata (EXIF/ICC), and downscale if needed."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Strip metadata by rebuilding the image from raw pixel data only.
    clean = Image.new("RGB", img.size)
    clean.putdata(list(img.getdata()))
    img = clean

    w, h = img.size
    if max(w, h) > max_dimension:
        scale = max_dimension / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))

    return img


def pil_to_base64_jpeg(img: Image.Image, quality: int = 90) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
