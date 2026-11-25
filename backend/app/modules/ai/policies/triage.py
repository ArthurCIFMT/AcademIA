from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from app.contracts.structured import StrictModel, digest


class Policy(StrictModel):
    schema_version: Literal[1] = 1
    version: Literal[1, 2] = 2
    minimum_age: Literal[18] = 18
    max_summary_chars: Annotated[int, Field(strict=True, ge=1, le=2400)] = 2400
    analysis_timeout_seconds: Annotated[float, Field(gt=0, le=25)] = 25
    analysis_attempts: Literal[1] = 1
    fonte_regras: Literal["onboarding-e-triagem-v1", "onboarding-e-triagem-v2"] = (
        "onboarding-e-triagem-v2"
    )

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.fonte_regras != f"onboarding-e-triagem-v{self.version}":
            raise ValueError("Versão da política incompatível com a fonte de regras.")
        return self

    @property
    def fingerprint(self) -> str:
        return digest(self.model_dump(mode="json"))
