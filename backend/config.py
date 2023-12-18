from orjson import loads, dumps, OPT_INDENT_2
from pydantic import BaseModel

from os import makedirs, urandom
from os.path import isfile, isdir


class Config(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    key: str = urandom(1024).hex()
    data_dir: str = "data"
    api_root_path: str = "/"
    discord_redirect_uri: str = ""
    discord_client_id: str = ""
    discord_client_secret: str = ""

if not isfile("config.json"):
    with open("config.json", "wb") as config_file:
        config_file.write(dumps(Config().model_dump(), option=OPT_INDENT_2))
    print("Please go to modify the config.json")
    exit(0)

config: Config
with open("config.json", "rb") as config_file:
    config = Config.model_validate(loads(config_file.read()))

HOST = config.host
PORT = config.port
KEY = config.key
DATA_DIR = config.data_dir
API_ROOT_PATH = config.api_root_path
DISCORD_REDIRECT_URI = config.discord_redirect_uri
DISCORD_CLIENT_ID = config.discord_client_id
DISCORD_CLIENT_SECRET = config.discord_client_secret

if not isdir(DATA_DIR):
    makedirs(DATA_DIR)
