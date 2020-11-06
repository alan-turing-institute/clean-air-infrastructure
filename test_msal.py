# import os
# import uuid
# import requests

# # from flask import Flask, render_template, session, request, redirect, url_for

# # from flask_session import Session  # https://pythonhosted.org/Flask-Session
# import msal

# CLIENT_ID = ""  # Application (client) ID of app registration
# CLIENT_SECRET = (
#     ""  # Placeholder - for use ONLY during testing.
# )
# # In a production app, we recommend you use a more secure method of storing your secret,
# # like Azure Key Vault. Or, use an environment variable as described in Flask's documentation:
# # https://flask.palletsprojects.com/en/1.1.x/config/#configuring-from-environment-variables
# # CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# # if not CLIENT_SECRET:
# #     raise ValueError("Need to define CLIENT_SECRET environment variable")

# # AUTHORITY = "https://login.microsoftonline.com/common"  # For multi-tenant app
# AUTHORITY = "https://login.microsoftonline.com/"
# REDIRECT_PATH = "https://localhost:8000/getAToken"  # Used for forming an absolute URL to your redirect URI.
# # The absolute URL must match the redirect URI you set
# # in the app's registration in the Azure portal.

# SESSION_TYPE = (
#     "filesystem"  # Specifies the token cache should be stored in server-side session
# )


# state = str(uuid.uuid4())

# ClientApp = msal.ConfidentialClientApplication(
#     CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET, token_cache=None,
# )

# print(
#     ClientApp.get_authorization_request_url(
#         scopes=[], state=state, redirect_uri=REDIRECT_PATH,
#     )
# )

