import os
from dotenv import load_dotenv


class Config:
    load_dotenv()

    ENV = "development"
    DEVELOPMENT = os.environ.get("DEBUG")

    USER_POOL_ID = os.environ.get("USER_POOL_ID")
    CLIENT_ID = os.environ.get("CLIENT_ID")
    USER_POOL_NAME = os.environ.get("USER_POOL_NAME")

    DB_HOST = os.environ.get("DB_HOST")
    DB_USERNAME = os.environ.get("DB_USERNAME")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME")

    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")