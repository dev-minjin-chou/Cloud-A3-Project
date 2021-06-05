import os
from dotenv import load_dotenv


class Config:
    load_dotenv()

    ENV = "development"
    DEVELOPMENT = os.environ.get("DEBUG")

    USER_POOL_ID = os.environ.get("USER_POOL_ID")
    CLIENT_ID = os.environ.get("CLIENT_ID")
    USER_POOL_NAME = os.environ.get("USER_POOL_NAME")

    DOCUMENTDB_CLUSTER_ENDPOINT = os.environ.get("DOCUMENTDB_CLUSTER_ENDPOINT")
    DOCUMENTDB_USERNAME = os.environ.get("DOCUMENTDB_USERNAME")
    DOCUMENTDB_PASSWORD = os.environ.get("DOCUMENTDB_PASSWORD")
