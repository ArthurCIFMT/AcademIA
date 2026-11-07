from typing import Annotated

from pydantic import Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(hide_input_in_errors=True)

    app_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        Field(validation_alias="ACADEMIA_APP_NAME")
    )
