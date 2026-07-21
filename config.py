import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")
FTP_REMOTE_DIR = os.getenv("FTP_REMOTE_DIR")

REPO_URL = os.getenv("REPO_URL")
REPO_FOLDER = os.getenv("REPO_FOLDER")

DOMAIN = os.getenv("DOMAIN")

NEW_IMAGES_FOLDER = os.getenv("NEW_IMAGES_FOLDER")
PROCESSED_IMAGES_FOLDER = os.getenv("PROCESSED_IMAGES_FOLDER")
IMAGES_FOLDER = os.getenv("IMAGES_FOLDER")
DOCUMENTS_FOLDER = os.getenv("DOCUMENTS_FOLDER")

COLLECTIONS_RAW = os.getenv("COLLECTIONS")
COLLECTIONS = [c.strip() for c in COLLECTIONS_RAW.split(",") if c.strip()]
