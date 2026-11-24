from typing import Annotated, Protocol, Self
from uuid import UUID

import httpx
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    SecretStr,
    ValidationError,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.modules.access.biometrics.images import MAX_IMAGE_BYTES


class FacialProviderError(Exception):
    """O provedor não confirmou a operação."""


class RejectedFace(ValueError):
    """A imagem não contém exatamente um rosto aceito."""


class FacialProvider(Protocol):
    @property
    def max_image_bytes(self) -> int: ...

    def validate_photo(self, image: bytes) -> None: ...

    def recognize(self, image: bytes) -> list["FaceCandidate"]: ...

    def add_example(self, subject: str, image: bytes) -> UUID: ...

    def list_examples(self, subject: str) -> list[UUID]: ...

    def delete_example(self, subject: str, image_id: UUID) -> None: ...


class CompreFaceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACADEMIA_COMPREFACE_",
        hide_input_in_errors=True,
        env_ignore_empty=True,
    )

    url: AnyHttpUrl | None = None
    detection_key: SecretStr | None = None
    recognition_key: SecretStr | None = None
    timeout_seconds: Annotated[float, Field(gt=0, le=30)] = 20
    detection_threshold: Annotated[float, Field(gt=0, le=1)] = 0.8
    max_image_bytes: Annotated[int, Field(ge=1024, le=MAX_IMAGE_BYTES)] = (
        MAX_IMAGE_BYTES
    )

    @model_validator(mode="after")
    def validate_connection(self) -> Self:
        if (
            self.url is None
            and self.detection_key is None
            and self.recognition_key is None
        ):
            return self
        if not self.url or not self.detection_key or not self.recognition_key:
            raise ValueError("Configure o endereço e as duas chaves do CompreFace.")
        if self.detection_key == self.recognition_key:
            raise ValueError("Use chaves distintas para detecção e reconhecimento.")
        url = self.url
        if (
            (
                url.scheme == "http"
                and url.host not in {"127.0.0.1", "localhost", "[::1]"}
            )
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/", None}
        ):
            raise ValueError("Use a origem HTTPS ou HTTP no loopback para CompreFace.")
        return self


class DetectionBox(BaseModel):
    probability: Annotated[float, Field(strict=True, ge=0, le=1)]


class DetectedFace(BaseModel):
    box: DetectionBox


class DetectionResult(BaseModel):
    result: list[DetectedFace]


class FaceCandidate(BaseModel):
    subject: Annotated[str, Field(min_length=1, max_length=120)]
    similarity: Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]


class RecognizedFace(DetectedFace):
    subjects: Annotated[list[FaceCandidate], Field(max_length=2)]


class RecognitionResult(BaseModel):
    result: list[RecognizedFace]


class FaceExample(BaseModel):
    image_id: UUID
    subject: str


class ExampleList(BaseModel):
    faces: list[FaceExample]
    total_elements: Annotated[int, Field(ge=0)]


class CompreFace:
    def __init__(
        self,
        settings: CompreFaceSettings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if (
            not settings.url
            or not settings.detection_key
            or not settings.recognition_key
        ):
            raise ValueError("CompreFace não configurado.")
        self._origin = str(settings.url)
        self._detection = settings.detection_key
        self._recognition = settings.recognition_key
        self._timeout = settings.timeout_seconds
        self._threshold = settings.detection_threshold
        self._max_bytes = settings.max_image_bytes
        self._transport = transport

    @property
    def max_image_bytes(self) -> int:
        return self._max_bytes

    def _request(
        self,
        method: str,
        path: str,
        *,
        detection: bool = False,
        params: dict[str, str] | None = None,
        image: bytes | None = None,
    ) -> httpx.Response:
        key = self._detection if detection else self._recognition
        files = (
            {"file": ("foto.jpg", image, "image/jpeg")} if image is not None else None
        )
        try:
            with httpx.Client(
                base_url=self._origin,
                timeout=self._timeout,
                trust_env=False,
                transport=self._transport,
            ) as client:
                return client.request(
                    method,
                    "/api/v1" + path,
                    params=params,
                    files=files,
                    headers={"x-api-key": key.get_secret_value()},
                )
        except httpx.HTTPError:
            raise FacialProviderError from None

    def validate_photo(self, image: bytes) -> None:
        response = self._request(
            "POST",
            "/detection/detect",
            detection=True,
            image=image,
            params={"limit": "0", "det_prob_threshold": str(self._threshold)},
        )
        faces = self._face_response(response, DetectionResult).result
        if len(faces) != 1 or faces[0].box.probability < self._threshold:
            raise RejectedFace

    def recognize(self, image: bytes) -> list[FaceCandidate]:
        self.validate_photo(image)
        response = self._request(
            "POST",
            "/recognition/recognize",
            image=image,
            params={
                "limit": "0",
                "prediction_count": "2",
                "detect_faces": "true",
                "det_prob_threshold": str(self._threshold),
            },
        )
        faces = self._face_response(response, RecognitionResult).result
        if len(faces) != 1 or faces[0].box.probability < self._threshold:
            raise RejectedFace
        return faces[0].subjects

    def _face_response[T: BaseModel](
        self, response: httpx.Response, schema: type[T]
    ) -> T:
        if response.status_code == 400:
            try:
                payload = response.json()
            except ValueError:
                raise FacialProviderError from None
            if isinstance(payload, dict) and payload.get("code") == 28:
                raise RejectedFace
        return self._decode(response, schema)

    @staticmethod
    def _decode[T: BaseModel](response: httpx.Response, schema: type[T]) -> T:
        if not response.is_success:
            raise FacialProviderError
        try:
            return schema.model_validate_json(response.content)
        except ValidationError:
            raise FacialProviderError from None

    def add_example(self, subject: str, image: bytes) -> UUID:
        response = self._request(
            "POST",
            "/recognition/faces",
            image=image,
            params={"subject": subject, "det_prob_threshold": str(self._threshold)},
        )
        example = self._decode(response, FaceExample)
        if example.subject != subject:
            raise FacialProviderError
        return example.image_id

    def list_examples(self, subject: str) -> list[UUID]:
        result = self._decode(
            self._request(
                "GET",
                "/recognition/faces",
                params={"subject": subject, "page": "0", "size": "20"},
            ),
            ExampleList,
        )
        if result.total_elements != len(result.faces) or any(
            face.subject != subject for face in result.faces
        ):
            raise FacialProviderError
        return [face.image_id for face in result.faces]

    def delete_example(self, subject: str, image_id: UUID) -> None:
        response = self._request("DELETE", f"/recognition/faces/{image_id}")
        if response.status_code == 404:
            if image_id not in self.list_examples(subject):
                return
            raise FacialProviderError
        example = self._decode(response, FaceExample)
        if example.subject != subject or example.image_id != image_id:
            raise FacialProviderError
