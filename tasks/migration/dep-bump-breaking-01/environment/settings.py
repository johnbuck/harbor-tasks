"""Application settings + helpers, written against Pydantic v1.

This module imports and runs under Pydantic v1 only. The installed Pydantic is
v2, so every v1-ism below is a breaking-change site that must be migrated.
"""

from typing import List, Optional

from pydantic import BaseSettings, Field, validator, root_validator


class AppSettings(BaseSettings):
    host: str = "localhost"
    port: int = 8080
    # v1 Field(env=...) — in pydantic v2 + pydantic-settings, env binding moved
    # to validation_alias / the settings config; `env=` is no longer accepted.
    log_level: str = Field("INFO", env="APP_LOG_LEVEL")
    # CSV string in the environment that must parse into a list.
    allowed_hosts: List[str] = Field(default_factory=list, env="APP_ALLOWED_HOSTS")
    workers: int = 4
    replica_port: Optional[int] = None

    # --- v1 field validator -------------------------------------------------
    @validator("port")
    def port_in_range(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("port must be in 1..65535")
        return v

    # --- v1 field validator with pre=True on a non-str-typed field ----------
    @validator("allowed_hosts", pre=True)
    def split_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v

    # --- v1 cross-field root validator --------------------------------------
    @root_validator
    def replica_defaults_to_port(cls, values):
        if values.get("replica_port") is None:
            values["replica_port"] = values.get("port")
        return values

    class Config:
        env_prefix = ""
        case_sensitive = False


def settings_as_dict(s: AppSettings) -> dict:
    # v1 serialization API.
    return s.dict()


def settings_from_mapping(data: dict) -> AppSettings:
    # v1 construction-from-mapping API.
    return AppSettings.parse_obj(data)
