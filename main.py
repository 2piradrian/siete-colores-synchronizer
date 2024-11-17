import os
import json
from ftplib import FTP
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")

DOCUMENTS_FOLDER = "documents"
DOCUMENTS_HOST = "/public_html/data"


def connect_to_mongo():
    try:
        connection_string = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_URL}/{MONGO_DB_NAME}"
        client = MongoClient(connection_string)
        return client
    except Exception as e:
        print(f"Error: {e}")


def export_collections(client, collections, output_folder):
    try:
        db = client[MONGO_DB_NAME]
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for collection in collections:
            col = db[collection]
            documents = list(col.find())

            # Convert ObjectId to string and if exists createdAt to string
            for document in documents:
                document["_id"] = str(document["_id"])
                if "createdAt" in document:
                    document["createdAt"] = str(document["createdAt"])

            with open(f"{output_folder}/{collection}.json", "w") as file:
                json.dump(documents, file, indent=4)
    except Exception as e:
        print(f"Error: {e}")


def upload_to_ftp(local_folder, remote_folder):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASSWORD)
        ftp.cwd(remote_folder)

        for filename in os.listdir(local_folder):
            if filename.endswith(".json"):
                local_filepath = os.path.join(local_folder, filename)
                with open(local_filepath, "rb") as file:
                    ftp.storbinary(f"STOR {filename}", file)
                print(f"Updated {filename}.")

        ftp.quit()
    except Exception as e:
        print(f"Error: {e}")


def main():
    client = connect_to_mongo()
    collections = ["products", "categories", "subcategories"]
    export_collections(client, collections, DOCUMENTS_FOLDER)
    upload_to_ftp(DOCUMENTS_FOLDER, DOCUMENTS_HOST)


if __name__ == "__main__":
    main()
