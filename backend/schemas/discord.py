from pydantic import BaseModel

from typing import Optional

class DiscordOAuth(BaseModel):
    token_type: str
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str

class DiscordUser(BaseModel):
    id: int
    username: str
    global_name: str
    avatar: Optional[str]