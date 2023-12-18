from pydantic import BaseModel, ConfigDict

from .discord import DiscordOAuth

class User(BaseModel):
    id: int
    username: str
    display_name: str
    avatar_url: str

class UserSecret(User):
    discord_oauth: DiscordOAuth
