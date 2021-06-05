import os
from dotenv import load_dotenv


class Config:
    load_dotenv()

    ENV = "development"
    DEVELOPMENT = True
    USER_POOL_ID = os.environ.get("USER_POOL_ID")
    CLIENT_ID = os.environ.get("CLIENT_ID")
    USER_POOL_NAME = os.environ.get("USER_POOL_NAME")
