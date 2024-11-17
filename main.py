import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

OUTPUT_FOLDER = "documents"


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


def main():
    client = connect_to_mongo()
    collections = ["products", "categories", "subcategories"]
    export_collections(client, collections, OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
