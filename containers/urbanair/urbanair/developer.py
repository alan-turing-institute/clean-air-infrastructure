"""UrbanAir API"""
import json

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import jwt
from jose.exceptions import JWTError
import requests

from .routers.developer import urbanroute
from .config import get_settings, AzureApp

azapp = AzureApp()
this_app_id = azapp.app_id
tenant_id = azapp.tenant_id
azure_directory = azapp.azure_directory

security = HTTPBasic()

def HTTPException401(detail):
    return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Basic"},
        )

def check_issuer(issuer):
    if issuer != f"https://sts.windows.net/{tenant_id}/":
        raise HTTPException401(f"Unrecognised issuer {issuer} in token")
    return issuer

def get_key(issuer, key_id):
    keys = requests.get(f"{issuer}/discovery/keys").json()['keys']
    decode_key = next(filter(lambda x: x['kid'] == key_id, keys), None)

    if not decode_key:
        raise HTTPException401("Unrecognised key in token")
    return decode_key

def check_roles(roles):
    if roles is None or 'premium_user_access' not in roles:
        raise HTTPException401("Unauthorised access")


def get_role(token: HTTPBasicCredentials = Depends(security)):

    header =  jwt.get_unverified_headers(token)
    key_id = header['kid']
    claims_decoded = jwt.get_unverified_claims(token)
    provider = claims_decoded['tid']

    iss = check_issuer(claims_decoded['iss'])
    decode_key = get_key(iss, key_id)

    try:
        token_decoded = jwt.decode(token, json.dumps(decode_key),
                                   audience=f"{azure_directory}/{this_app_id}",
                                   issuer=iss,
                                   algorithms=header['alg'])
    except JWTError:
        raise HTTPException401("Unauthorised access - token signature non recognised")


    roles = check_roles(claims_decoded.get('roles'))
    #return claims_decoded.get('name', "user")

async def get_token(request: Request):
    token = request.headers['authorization'].split()[1]
    get_role(token)




app = FastAPI(
    title="Developer API",
    description="Provides routes not yet exposed to the public and tools for developers",
    version="0.0.1",
    root_path=get_settings().root_path,
)


app.include_router(urbanroute.router, tags=["Developer"],
                   dependencies=[Depends(get_token)])
