
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "enfermeria_escolar"
    DB_USER: str = "postgres"
    DB_PASSWORD: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        gt=0,
        le=1440,
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validar_clave_jwt(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET_KEY debe tener al menos 32 caracteres."
            )

        if value.strip() != value:
            raise ValueError(
                "JWT_SECRET_KEY no debe tener espacios al inicio o al final."
            )

        if value.lower() in {
            "secret",
            "changeme",
            "change-me",
            "your-secret-key",
            "clave-secreta",
        }:
            raise ValueError(
                "JWT_SECRET_KEY debe ser una clave segura y única."
            )

        return value

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validar_algoritmo_jwt(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError(
                "JWT_ALGORITHM debe ser HS256."
            )

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
