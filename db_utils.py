import json
from pymongo import MongoClient
from config import (
    MONGO_USER,
    MONGO_PASSWORD,
    MONGO_URL,
    MONGO_DB_NAME,
    COLLECTIONS,
    DOCUMENTS_FOLDER,
)

def connect_to_mongo():
    """Conecta a la base de datos de MongoDB y retorna el cliente."""
    try:
        connection_string = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_URL}/{MONGO_DB_NAME}"
        client = MongoClient(connection_string)
        client.server_info()
        return client
    except Exception as e:
        print(f"Error: {e}")
        return None

def export_collections(client):
    """Exporta las colecciones de MongoDB a archivos JSON."""
    if not client:
        print("No hay cliente de MongoDB activo para exportar colecciones.")
        return
    try:
        db = client[MONGO_DB_NAME]

        for collection in COLLECTIONS:
            col = db[collection]
            documents = list(col.find())

            for document in documents:
                document["_id"] = str(document["_id"])
                if "createdAt" in document:
                    document["createdAt"] = str(document["createdAt"])

            with open(f"{DOCUMENTS_FOLDER}/{collection}.json", "w") as file:
                json.dump(documents, file, indent=4)
    except Exception as e:
        print(f"Error: {e}")
