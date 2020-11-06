"""OAUTH Login for Odysseus"""
import logging
import uuid
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import msal
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

auth_settings = AuthSettings(
    client_id="", client_secret="", authority="https://login.microsoftonline.com/",
)


@app.get("/login")
def login():

    REDIRECT_PATH = "http://localhost:8000/getAToken"

    state = str(uuid.uuid4())

    # return "hi"
    auth_request_url = msal.ConfidentialClientApplication(
        str(auth_settings.client_id),
        authority=auth_settings.authority,
        client_credential=auth_settings.client_secret.get_secret_value(),
        token_cache=None,
    ).get_authorization_request_url(scopes=[], state=state, redirect_uri=REDIRECT_PATH,)

    return RedirectResponse(url=auth_request_url)


@app.get("/getAToken")  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized(code: str):

    # auth_code = request.query_params.get("code")
    auth_code = code

    if auth_code:
        result = msal.ConfidentialClientApplication(
            str(auth_settings.client_id),
            authority=auth_settings.authority,
            client_credential=auth_settings.client_secret.get_secret_value(),
            token_cache=None,
        ).acquire_token_by_authorization_code(
            auth_code,
            scopes=[],  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri="http://localhost:8000/getAToken",
        )

        print(result)
        return result.get("access_token")
        # print(result.get("refresh_token"))

        # print(auth_settings.client_secret.get_secret_value())


# if request.args.get("state") != session.get("state"):
#     return redirect(url_for("index"))  # No-OP. Goes back to Index page
# if "error" in request.args:  # Authentication/Authorization failure
#     return render_template("auth_error.html", result=request.args)
# if request.args.get("code"):
#     cache = _load_cache()
#     result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
#         request.args["code"],
#         scopes=app_config.SCOPE,  # Misspelled scope would cause an HTTP 400 error here
#         redirect_uri=url_for("authorized", _external=True),
#     )
#     if "error" in result:
#         return render_template("auth_error.html", result=result)
#     session["user"] = result.get("id_token_claims")
#     _save_cache(cache)
# return redirect(url_for("index"))
