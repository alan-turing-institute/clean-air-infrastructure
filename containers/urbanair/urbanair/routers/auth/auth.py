"""
Authentication via MS routes
"""
from datetime import timedelta, datetime
from urllib.parse import urlencode
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseSettings, BaseModel
from authlib.integrations.starlette_client import OAuth
from ...config import AuthSettings, auth_templates
from ...security import logged_in

router = APIRouter()
auth_settings = AuthSettings()


class Token(BaseModel):
    access_token: str
    token_type: str


# Register Azure AAD
oauth = OAuth()
oauth.register(
    name="azure",
    client_id=str(auth_settings.client_id),
    client_secret=auth_settings.client_secret.get_secret_value(),
    access_token_url=auth_settings.authority + "/oauth2/v2.0/token",
    access_token_params=None,
    authorize_url=auth_settings.authority + "/oauth2/v2.0/authorize",
    authorize_params=None,
    client_kwargs={"scope": "openid offline_access profile"},
    server_metadata_url=auth_settings.authority
    + "/v2.0/.well-known/openid-configuration",
)


# Define Authentication Routes


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.access_token_secret.get_secret_value(),
        algorithm=auth_settings.access_token_algorithm,
    )
    return encoded_jwt


@router.get("/auth/token", response_model=Token, include_in_schema=False)
def odysseus_token(user=Depends(logged_in)):

    access_token_expires = timedelta(minutes=auth_settings.access_token_expire_minutes)

    access_token = create_access_token(
        data={"sub": user["preferred_username"], "roles": user["groups"]},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/", include_in_schema=False)
async def home():
    return HTMLResponse('<a href="/login">login</a>')


@router.get("/user", include_in_schema=False)
async def user_home(request: Request, user=Depends(logged_in)):

    return auth_templates.TemplateResponse(
        "auth.html", {"request": request, "user": user}
    )


@router.route("/login", include_in_schema=False)
async def login(request: Request):

    redirect_uri = request.url_for("authorized")

    if "http://0.0.0.0" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://0.0.0.0", "http://localhost")
    if "http://127.0.0.1" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://127.0.0.1", "http://localhost")

    return await oauth.azure.authorize_redirect(request, redirect_uri)


@router.get(
    "/getAToken", include_in_schema=False,
)  # Its absolute URL must match your app's redirect_uri set in AAD
async def authorized(request: Request):

    token = await oauth.azure.authorize_access_token(request)
    user = await oauth.azure.parse_id_token(request, token)
    request.session["user"] = dict(user)
    return RedirectResponse(url=request.url_for("user_home"))


@router.route("/logout", include_in_schema=False)
async def logout(request: Request, _=Depends(logged_in)):

    request.session.pop("user", None)
    return RedirectResponse(url=request.url_for("home"))
