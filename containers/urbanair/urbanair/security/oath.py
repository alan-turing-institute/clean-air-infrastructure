from typing import Optional, List
from uuid import UUID
from enum import Enum, unique
from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes
from pydantic import BaseModel, ValidationError
from jose import JWTError, jwt, ExpiredSignatureError
from urbanair.config.auth_config import AuthTokenSettings
from ..config import AuthTokenSettings


class RequiresLoginException(Exception):
    pass


class UserLogged:
    async def __call__(self, request: Request):

        user = request.session.get("user")
        if user:
            return user
        raise RequiresLoginException


logged_in = UserLogged()


@unique
class Roles(Enum):

    basic = UUID("2bdb89cb-7049-408a-a666-b1a176ad9b04")
    enhanced = UUID("4452e7b5-332a-460d-884a-02d8936b0476")
    admin = UUID("fa40b0d6-1c15-48cb-b2d4-4c6cff72502d")


class TokenData(BaseModel):
    username: str
    roles: List[UUID]


auth_settings = AuthTokenSettings()
bearer_scheme = HTTPBearer()


async def get_bearer_user(
    security_roles: SecurityScopes,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):

    token = credentials.credentials

    if security_roles.scopes:
        authenticate_value = f'Bearer roles="{security_roles.scope_str}"'
    else:
        authenticate_value = f"Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication Error: Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    credentials_timeout_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication Error: Credentials have expired",
        headers={"WWW-Authenticate": authenticate_value},
    )

    # Validate the token and get payload
    try:
        payload = jwt.decode(
            token,
            auth_settings.access_token_secret.get_secret_value(),
            algorithms=[auth_settings.access_token_algorithm],
        )
        username: str = payload.get("sub")
        roles = payload.get("roles", [])
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, roles=roles)
    except (JWTError, ValidationError) as e:
        if isinstance(e, ExpiredSignatureError):
            raise credentials_timeout_exception
        raise credentials_exception

    for role in security_roles.scopes:

        role_uuid = UUID(role)
        if role_uuid in token_data.roles:
            return token_data

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not enough permissions to access this resource",
        headers={"WWW-Authenticate": authenticate_value},
    )


async def oauth_basic_user(
    user: TokenData = Security(
        get_bearer_user,
        scopes=[Roles.admin.value.hex, Roles.enhanced.value.hex, Roles.basic.value.hex],
    )
) -> TokenData:

    return user


async def oauth_enhanced_user(
    user: TokenData = Security(
        get_bearer_user, scopes=[Roles.admin.value.hex, Roles.enhanced.value.hex]
    )
) -> TokenData:

    return user


async def oauth_admin_user(
    user: TokenData = Security(get_bearer_user, scopes=[Roles.admin.value.hex])
) -> TokenData:

    return user
