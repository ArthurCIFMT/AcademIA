import re
from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from os import replace
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BASE64 = ((MAX_IMAGE_BYTES + 2) // 3) * 4
MAX_INPUT_DIMENSION = 2048
MAX_OUTPUT_DIMENSION = 1200


class InvalidEquipmentImage(ValueError):
    pass


def normalize_image(encoded: str) -> bytes:
    if len(encoded) > MAX_IMAGE_BASE64:
        raise InvalidEquipmentImage
    try:
        content = b64decode(encoded, validate=True)
        if not content or len(content) > MAX_IMAGE_BYTES:
            raise InvalidEquipmentImage
        with Image.open(BytesIO(content), formats=["JPEG", "PNG"]) as source:
            if max(source.size) > MAX_INPUT_DIMENSION or getattr(
                source, "is_animated", False
            ):
                raise InvalidEquipmentImage
            oriented = ImageOps.exif_transpose(source)
            mode = (
                "RGBA"
                if "A" in oriented.getbands() or "transparency" in oriented.info
                else "RGB"
            )
            with oriented.convert(mode) as image:
                image.info.clear()
                image.thumbnail((MAX_OUTPUT_DIMENSION, MAX_OUTPUT_DIMENSION))
                output = BytesIO()
                image.save(output, format="PNG")
                return output.getvalue()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise InvalidEquipmentImage from None


class EquipmentImageStorage(Protocol):
    def store(self, image: bytes) -> str: ...

    def read(self, reference: str) -> bytes | None: ...


class LocalEquipmentImages:
    def __init__(self, root: Path) -> None:
        self.root = root

    def store(self, image: bytes) -> str:
        reference = sha256(image).hexdigest()
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / (reference + ".png")
        if target.is_file():
            return reference
        with NamedTemporaryFile(dir=self.root, delete=False) as temporary:
            path = Path(temporary.name)
            try:
                temporary.write(image)
                temporary.close()
                replace(path, target)
            finally:
                path.unlink(missing_ok=True)
        return reference

    def read(self, reference: str) -> bytes | None:
        if re.fullmatch(r"[0-9a-f]{64}", reference) is None:
            return None
        try:
            return (self.root / (reference + ".png")).read_bytes()
        except FileNotFoundError:
            return None
