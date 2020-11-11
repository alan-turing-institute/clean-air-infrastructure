"""OAUTH Login for Odysseus"""
from typing import Optional
import logging
from urllib.parse import urlencode
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import timedelta, datetime
from jose import JWTError, jwt
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from pydantic import BaseModel
from .config import get_settings, AuthSettings

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

app = FastAPI(
    title="My",
    description="High resolution air pollution forecasts",
    version="0.0.1",
    root_path=get_settings().root_path,
)


sentry_dsn = get_settings().sentry_dsn  # pylint: disable=C0103
if sentry_dsn:
    sentry_sdk.init(dsn=get_settings().sentry_dsn)
    app.add_middleware(SentryAsgiMiddleware)
    logger.info("Adding sentry logging middleware")
else:
    logging.warning("Sentry is not logging errors")

auth_settings = AuthSettings()

app.add_middleware(
    SessionMiddleware, secret_key=auth_settings.session_secret.get_secret_value()
)


class Token(BaseModel):
    access_token: str
    token_type: str


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

app.mount(
    "/static",
    StaticFiles(directory=str((Path(__file__).parent / "static").absolute())),
    name="static",
)
templates = Jinja2Templates(
    directory=str((Path(__file__).parent / "templates" / "auth").absolute())
)


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


@app.get("/auth/token", response_model=Token)
def odysseus_token(request: Request):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication Error: Could not validate credentials. Ensure user logged in.",
    )

    user = request.session.get("user")
    if user:
        access_token_expires = timedelta(
            minutes=auth_settings.access_token_expire_minutes
        )

        access_token = create_access_token(
            data={"sub": user["preferred_username"], "roles": user["groups"]},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}

    raise credentials_exception


@app.get("/")
async def welcome():
    return HTMLResponse('<a href="/login">login</a>')


@app.get("/home")
async def home(request: Request):

    user = request.session.get("user")
    if not user:
        return RedirectResponse(url=request.url_for("welcome"))

    return templates.TemplateResponse("auth.html", {"request": request, "user": user})


@app.route("/login")
async def login(request: Request):

    redirect_uri = request.url_for("authorized")

    if "http://0.0.0.0" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://0.0.0.0", "http://localhost")

    return await oauth.azure.authorize_redirect(request, redirect_uri)


@app.get("/getAToken")  # Its absolute URL must match your app's redirect_uri set in AAD
async def authorized(request: Request):

    token = await oauth.azure.authorize_access_token(request)
    user = await oauth.azure.parse_id_token(request, token)

    request.session["user"] = dict(user)
    return RedirectResponse(url=request.url_for("home"))


@app.route("/logout")
async def logout(request: Request):

    request.session.pop("user", None)
    end_session_base_uri = (await oauth.azure.load_server_metadata())[
        "end_session_endpoint"
    ]
    return_to = urlencode({"post_logout_redirect_uri": request.url_for("welcome")})
    logout_uri = end_session_base_uri + "?" + return_to

    return RedirectResponse(url=logout_uri)
