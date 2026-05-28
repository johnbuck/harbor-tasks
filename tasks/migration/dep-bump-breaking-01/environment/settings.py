from pydantic import BaseSettings


class AppSettings(BaseSettings):
    host: str = "localhost"
    port: int = 8080
