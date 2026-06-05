"""Place for all settings classes for the Maintenance Page."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MaintenancePageSettings(BaseSettings):
    """Settings for the Customizer API."""

    status_url: str | None = Field(default=None)

    title: str = Field(default="Maintenance Mode")
    text: str = Field(default="The Content Management system is currently unavailable.")
    footer: str = Field(default="")

    loglevel: Literal["INFO", "DEBUG", "WARNING", "ERROR"] = "INFO"
    host: str | list[str] = Field(default=["::", "0.0.0.0"], frozen=True)  # noqa: S104
    port: int = Field(default=5555, frozen=True)
    templates_dir: str = Field(default=str(Path(str(Path(str(Path(__file__).resolve()).parent))) / "templates"))

    model_config = SettingsConfigDict(env_prefix="MAINTENANCE_PAGE_")


# Create instance of the settings class
settings = MaintenancePageSettings()
