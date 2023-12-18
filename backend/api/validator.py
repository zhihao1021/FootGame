from aiofile import async_open
from aiohttp import ClientSession
from fastapi import Depends, Request
from fastapi.security.utils import get_authorization_scheme_param
from jwt import encode, decode
from orjson import loads, dumps, OPT_INDENT_2
from pydantic import BaseModel

from datetime import datetime, timedelta, timezone
from os import makedirs
from os.path import isdir, join

from config import (
    DATA_DIR,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
    KEY,
)
from schemas.discord import DiscordOAuth, DiscordUser
from schemas.user import User, UserSecret

from .exceptions import UNAUTHORIZE

USER_DIR = join(DATA_DIR, "users")
if not isdir(USER_DIR):
    makedirs(USER_DIR)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

async def get_header_token(request: Request):
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise UNAUTHORIZE
    return param

async def discord_auth(code: str) -> DiscordOAuth:
    async with ClientSession() as session:
        response = await session.post(
            "https://discord.com/api/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        if response.status != 200:
            raise UNAUTHORIZE
        content = await response.content.read()

        discord_oauth =  DiscordOAuth.model_validate(loads(content))
        discord_oauth.expires_in += int(datetime.now().timestamp())
        return discord_oauth

async def fetch_user(data: DiscordOAuth) -> UserSecret:
    async with ClientSession() as session:
        if datetime.now().timestamp() > data.expires_in:
            response = await session.get(
                "https://discord.com/api/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": data.refresh_token,
                    "client_id": DISCORD_CLIENT_ID,
                    "client_secret": DISCORD_CLIENT_SECRET
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            if response.status != 200:
                raise UNAUTHORIZE
            content = await response.content.read()

            data =  DiscordOAuth.model_validate(loads(content))
            data.expires_in += int(datetime.now().timestamp())
        response = await session.get(
            "https://discord.com/api/users/@me",
            headers={
                "Authorization": f"{data.token_type} {data.access_token}"
            }
        )
        if response.status != 200:
            raise UNAUTHORIZE
        content = await response.content.read()

    discord_user = DiscordUser.model_validate(loads(content))
    user_secret = UserSecret(
        id=discord_user.id,
        username=discord_user.username,
        display_name=discord_user.global_name,
        avatar_url=f"https://cdn.discordapp.com/avatars/{discord_user.id}/{discord_user.avatar}.png" if discord_user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
        discord_oauth=data
    )

    async with async_open(f"{join(USER_DIR, str(user_secret.id))}.json", "wb") as user_file:
        await user_file.write(dumps(user_secret.model_dump(), option=OPT_INDENT_2))
    
    return user_secret

def gen_jwt(user: User) -> Token:
    data = user.model_dump()
    data["exp"] = datetime.now(timezone.utc) + timedelta(days=3)
    return Token(
        access_token=encode(data, key=KEY, algorithm="HS256")
    )

async def user_login(code: str) -> str:
    discord_oauth = await discord_auth(code=code)
    user_secret = await fetch_user(data=discord_oauth)
    return gen_jwt(user=User.model_validate(user_secret.model_dump(exclude=["discord_oauth"])))

def get_user(token: str = Depends(get_header_token)) -> User:
    try:
        return User.model_validate(
            decode(token, key=KEY, algorithms=["HS256"])
        )
    except:
        raise UNAUTHORIZE

async def refresh_user(token: str = Depends(get_header_token)) -> Token:
    try:
        user = User.model_validate(
            decode(token, key=KEY, algorithms=["HS256"], options={"verify_exp": False})
        )
        async with async_open(f"{join(USER_DIR, str(user.id))}.json", "rb") as user_file:
            user_secret = UserSecret.model_validate(loads(await user_file.read()))
        user = await fetch_user(data=user_secret.discord_oauth)
        return gen_jwt(user=User.model_validate(user.model_dump(exclude=["discord_oauth"])))
    except:
        raise UNAUTHORIZE

