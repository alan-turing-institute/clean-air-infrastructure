"""Configurations"""
from uuid import UUID

from pydantic import BaseSettings, HttpUrl, SecretStr


class AuthTokenSettings(BaseSettings):
    """Settings for generating jwt tokens"""

    access_token_secret: SecretStr
    access_token_algorithm: str = "HS256"
    access_token_expire_minutes: int

    class Config:  # pylint: disable=C0115
        env_file = ".env"
        env_file_encoding = "utf-8"


class AuthSettings(AuthTokenSettings):
    """Settings class"""

    client_id: UUID
    client_secret: SecretStr
    tenant_id: UUID
    base_url: HttpUrl
    session_secret: SecretStr

    @property
    def authority(self):
        """Makes authorised URL"""
        return self.base_url + str(self.tenant_id)
