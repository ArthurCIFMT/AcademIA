from base64 import b64decode
from io import BytesIO

from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BASE64 = (MAX_IMAGE_BYTES + 2) // 3 * 4
MAX_DIMENSION = 4096


class InvalidFaceImage(ValueError):
    pass


def clean_face_image(encoded: str, *, max_bytes: int) -> bytes:
    try:
        content = b64decode(encoded, validate=True)
        if not content or len(content) > max_bytes:
            raise InvalidFaceImage
        with Image.open(BytesIO(content), formats=["JPEG", "PNG"]) as source:
            if max(source.size) > MAX_DIMENSION or getattr(
                source, "is_animated", False
            ):
                raise InvalidFaceImage
            with ImageOps.exif_transpose(source).convert("RGB") as image:
                image.info.clear()
                image.thumbnail((1600, 1600))
                output = BytesIO()
                image.save(output, format="JPEG", quality=90)
                return output.getvalue()
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError):
        raise InvalidFaceImage from None
