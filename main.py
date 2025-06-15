import io
import os
import json
import stat
import shutil
import subprocess
from PIL import Image
from ftplib import FTP
from dotenv import load_dotenv
from pymongo import MongoClient
from multiprocessing import Pool, cpu_count


load_dotenv()

# --- --- --- Constants --- --- --- #
MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")

REPO_URL = "https://github.com/2piradrian/siete-colores-web"
REPO_FOLDER = "./web"

USER_IMAGES_FOLDER = "./images"
IMAGES_FOLDER = "./web/static/assets/product-images"
DOCUMENTS_FOLDER = "./web/static/data"

COLLECTIONS = ["products", "categories", "subcategories"]
# --- --- --- --------- --- --- --- #


# Cambia los permisos de todos los archivos y carpetas dentro de 'folder'.
def change_permissions(folder):
    for root, dirs, files in os.walk(folder):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IWRITE)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IWRITE)


# Cambia permisos y elimina archivos protegidos.
def delete_with_permissions(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


# Clona el repositorio de GitHub y maneja permisos.
def clone_repo():
    try:
        if os.path.exists(REPO_FOLDER):
            change_permissions(REPO_FOLDER)
            shutil.rmtree(REPO_FOLDER, onerror=delete_with_permissions)

        subprocess.run(["git", "clone", REPO_URL, REPO_FOLDER], check=True)
    except Exception as e:
        print(f"Error: {e}")


# Connecta a la base de datos de MongoDB y retorna el cliente.
def connect_to_mongo():
    try:
        connection_string = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_URL}/{MONGO_DB_NAME}"
        client = MongoClient(connection_string)
        client.server_info()
        return client

    except Exception as e:
        print(f"Error: {e}")
        return None


# Exporta las colecciones de MongoDB a archivos JSON.
def export_collections(client):
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


# Procesa la imagen
def process_image(file_info):
    original_image_path, webp_image_path = file_info
    try:
        with Image.open(original_image_path) as img:
            if hasattr(img, '_getexif') and img._getexif():
                exif = dict(img._getexif().items())
                orientation = exif.get(274, 1)
                # Rotación según EXIF
                if orientation == 2:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    img = img.transpose(Image.ROTATE_180)
                elif orientation == 4:
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                elif orientation == 5:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
                elif orientation == 6:
                    img = img.transpose(Image.ROTATE_270)
                elif orientation == 7:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
                elif orientation == 8:
                    img = img.transpose(Image.ROTATE_90)
            img = img.convert("RGB")
            save_image_with_target_size(img, webp_image_path, target_kb=120, min_quality=5, max_quality=95)
    except Exception as e:
        print(f"Error al procesar imagen {original_image_path}: {e}")


# Guarda una imagen WebP ajustando la calidad para no superar el peso objetivo.
def save_image_with_target_size(img, output_path, target_kb, min_quality, max_quality):
    target_bytes = target_kb * 1024
    best_quality = min_quality
    best_data = None

    low = min_quality
    high = max_quality

    while low <= high:
        mid = ((low + high) // 2) // 5 * 5  # Pasos de 5 en 5
        buffer = io.BytesIO()
        img.save(buffer, format="WebP", quality=mid, method=6, lossless=False)
        size = buffer.tell()

        if size <= target_bytes:
            best_quality = mid
            best_data = buffer.getvalue()
            low = mid + 5 # Pasos de 5 en 5
        else:
            high = mid - 5 # Pasos de 5 en 5

    if best_data:
        with open(output_path, "wb") as f:
            f.write(best_data)
        print(f"Guardado {output_path} con calidad {best_quality} ({len(best_data) // 1024} KB)")
    else:
        img.save(output_path, "WebP", quality=min_quality, method=6, lossless=False)
        print(f"Guardado {output_path} con calidad mínima ({min_quality}).")


# Copia las imágenes desde la carpeta 'images' a 'product-images' y las convierte a WebP manteniendo su orientación.
def copy_and_convert_images():
    try:
        if not os.path.exists(IMAGES_FOLDER):
            os.makedirs(IMAGES_FOLDER)

        image_tasks = []
        for root, dirs, files in os.walk(USER_IMAGES_FOLDER):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg", ".png")):
                    original_image_path = os.path.join(root, file)
                    webp_image_path = os.path.join(IMAGES_FOLDER, os.path.splitext(file)[0] + ".webp")
                    image_tasks.append((original_image_path, webp_image_path))

        print(f"Procesando {len(image_tasks)} imágenes en paralelo...")
        with Pool(cpu_count()) as pool:
            pool.map(process_image, image_tasks)

    except Exception as e:
        print(f"Error al copiar y convertir imágenes: {e}")


# Construye el sitio web utilizando npm.
def build_site():
    try:
        subprocess.run(["npm", "i"], cwd=os.path.abspath(REPO_FOLDER), check=True, shell=True)
        subprocess.run(["npm", "run", "build"], cwd=os.path.abspath(REPO_FOLDER), check=True, shell=True)

    except Exception as e:
        print(f"Error: {e}")


# Sube el contenido de la carpeta 'public' al servidor FTP.
def upload_to_ftp():
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASSWORD)
        print(f"Conexión exitosa a {FTP_HOST}")

        ftp.cwd("/domains/sietecolores3d.com.ar/public_html")
        print(f"Cambiado a directorio de producción: {ftp.pwd()}")

        public_folder = os.path.join(REPO_FOLDER, "public")
        print(f"Subiendo archivos desde: {public_folder}")

        def upload_directory(local_dir, remote_dir):
            current_dir = ftp.pwd()
            try:
                ftp.cwd(remote_dir)
            except:
                print(f"Creando directorio: {remote_dir}")
                try:
                    ftp.mkd(remote_dir)
                    ftp.cwd(remote_dir)
                except Exception as e:
                    print(f"Error al crear directorio {remote_dir}: {e}")
                    return False

            print(f"Procesando directorio: {local_dir} -> {ftp.pwd()}")

            for item in os.listdir(local_dir):
                local_path = os.path.join(local_dir, item)

                if os.path.isdir(local_path):
                    upload_directory(local_path, item)
                else:
                    try:
                        with open(local_path, 'rb') as file:
                            result = ftp.storbinary(f'STOR {item}', file)
                            print(f"Subido: {local_path} -> {ftp.pwd()}/{item}")
                    except Exception as e:
                        print(f"Error al subir {local_path}: {e}")

            ftp.cwd(current_dir)
            return True

        success = upload_directory(public_folder, ".")

        if success:
            print("Todos los archivos han sido subidos correctamente.")
        else:
            print("Hubo errores durante la subida de archivos.")

        ftp.quit()
        print("Proceso completado.")

    except Exception as e:
        print(f"Error general: {e}")


def main():
    print("Cargando...")
    clone_repo()
    client = connect_to_mongo()
    export_collections(client)
    copy_and_convert_images()
    build_site()
    upload_to_ftp()


if __name__ == "__main__":
    main()
