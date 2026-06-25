#!/bin/bash
# Reference solution — fully migrates settings.py from Pydantic v1 to v2 +
# pydantic-settings. Each edit below corresponds to one graded migration site.
set -e

pip install --no-cache-dir pydantic-settings==2.7.1

cat > /app/settings.py <<'EOF'
"""Application settings + helpers, migrated to Pydantic v2 + pydantic-settings."""

from typing import Annotated, List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class AppSettings(BaseSettings):
    host: str = "localhost"
    port: int = 8080
    log_level: str = Field("INFO", validation_alias="APP_LOG_LEVEL")
    # NoDecode stops pydantic-settings from JSON-decoding the env value so the
    # mode="before" validator below can split the CSV string itself.
    allowed_hosts: Annotated[List[str], NoDecode] = Field(
        default_factory=list, validation_alias="APP_ALLOWED_HOSTS"
    )
    workers: int = 4
    replica_port: Optional[int] = None

    @field_validator("port")
    @classmethod
    def port_in_range(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("port must be in 1..65535")
        return v

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def split_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v

    @model_validator(mode="after")
    def replica_defaults_to_port(self):
        if self.replica_port is None:
            self.replica_port = self.port
        return self

    # populate_by_name lets the aliased fields still be set by their Python name
    # (e.g. AppSettings(allowed_hosts=...)), matching v1 behavior where Field(env=)
    # named the env var but left the attribute name usable for direct construction.
    model_config = SettingsConfigDict(
        env_prefix="", case_sensitive=False, populate_by_name=True
    )


def settings_as_dict(s: AppSettings) -> dict:
    return s.model_dump()


def settings_from_mapping(data: dict) -> AppSettings:
    return AppSettings.model_validate(data)
EOF
