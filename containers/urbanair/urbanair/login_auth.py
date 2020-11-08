"""OAUTH Login for Odysseus"""
import logging
import uuid
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
import json
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import msal
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from .config import get_settings, AuthSettings

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

app = FastAPI(
    title="My",
    description="High resolution air pollution forecasts",
    version="0.0.1",
    root_path=get_settings().root_path,
)
app.add_middleware(SessionMiddleware, secret_key="")

sentry_dsn = get_settings().sentry_dsn  # pylint: disable=C0103
if sentry_dsn:
    sentry_sdk.init(dsn=get_settings().sentry_dsn)
    app.add_middleware(SentryAsgiMiddleware)
    logger.info("Adding sentry logging middleware")
else:
    logging.warning("Sentry is not logging errors")

auth_settings = AuthSettings()

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


@app.get("/auth/token")
def odysseus_token(request: Request):

    user = request.session.get("user")
    if user:
        return {"token": "asdfasdfasdgssh.adfgasdfg"}
    else:
        return "Fail"


@app.route("/")
def token_mint(request: Request):
    user = request.session.get("user")
    if user:
        print(user)
        return templates.TemplateResponse(
            "auth.html", {"request": request, "user": user}
        )
    return HTMLResponse('<a href="/login">login</a>')


@app.get("/login")
async def login(request: Request):

    redirect_uri = request.url_for("authorized")
    return await oauth.azure.authorize_redirect(request, redirect_uri)


@app.get("/getAToken")  # Its absolute URL must match your app's redirect_uri set in AAD
async def authorized(request: Request):

    token = await oauth.azure.authorize_access_token(request)
    user = await oauth.azure.parse_id_token(request, token)

    request.session["user"] = dict(user)
    return RedirectResponse(url=request.url_for("token_mint"))


@app.route("/logout")
async def logout(request: Request):

    request.session.pop("user", None)
    return RedirectResponse(url=request.url_for("token_mint"))
