import io
import os
import shutil
from PIL import Image
from multiprocessing import Pool, cpu_count
from config import NEW_IMAGES_FOLDER, PROCESSED_IMAGES_FOLDER, IMAGES_FOLDER

def save_image_with_target_size(img, output_path, target_kb=95, min_quality=5, max_quality=100):
    """Guarda una imagen WebP ajustando la calidad para no superar el peso objetivo."""
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
            low = mid + 5  # Pasos de 5 en 5
        else:
            high = mid - 5  # Pasos de 5 en 5

    if best_data:
        with open(output_path, "wb") as f:
            f.write(best_data)
        print(f"Guardado {output_path} con calidad {best_quality} ({len(best_data) // 1024} KB).")
    else:
        img.save(output_path, "WebP", quality=min_quality, method=6, lossless=False)
        print(f"Guardado {output_path} con calidad mínima ({min_quality}).")

def process_image(file_info):
    """Procesa la imagen y la guarda ajustando calidad/rotación."""
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
            save_image_with_target_size(img, webp_image_path, target_kb=95, min_quality=5, max_quality=100)
    except Exception as e:
        print(f"Error al procesar imagen {original_image_path}: {e}")

def copy_and_convert_images():
    """Convierte a WebP manteniendo su orientación, y las envía a la carpeta web."""
    try:
        if not os.path.exists(IMAGES_FOLDER):
            os.makedirs(IMAGES_FOLDER)

        if not os.path.exists(NEW_IMAGES_FOLDER):
            print(f"La carpeta {NEW_IMAGES_FOLDER} no existe. Nada que procesar.")
            return

        if not os.path.exists(PROCESSED_IMAGES_FOLDER):
            os.makedirs(PROCESSED_IMAGES_FOLDER)

        # --- Armar lista de tareas (entrada -> salida en ./images) ---
        image_tasks = []
        for root, dirs, files in os.walk(NEW_IMAGES_FOLDER):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg", ".png")):
                    src = os.path.join(root, file)
                    dst = os.path.join(
                        PROCESSED_IMAGES_FOLDER, os.path.splitext(file)[0] + ".webp"
                    )
                    image_tasks.append((src, dst))

        print(f"Procesando {len(image_tasks)} imágenes en paralelo...")

        with Pool(cpu_count()) as pool:
            pool.map(process_image, image_tasks)

        # --- Copiar todas las imágenes procesadas a ./web/... ---
        for file in os.listdir(PROCESSED_IMAGES_FOLDER):
            if file.lower().endswith(".webp"):
                src = os.path.join(PROCESSED_IMAGES_FOLDER, file)
                dst = os.path.join(IMAGES_FOLDER, file)
                shutil.copy2(src, dst)
                print(f"Copiado: {src} -> {dst}")

        # --- Limpiar carpeta new-images (solo los originales) ---
        for root, dirs, files in os.walk(NEW_IMAGES_FOLDER):
            for file in files:
                os.remove(os.path.join(root, file))
        print("Carpeta new-images limpiada.")

    except Exception as e:
        print(f"Error en copy_and_convert_images: {e}")
