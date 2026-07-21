import os
import stat
import shutil
import subprocess
from config import REPO_URL, REPO_FOLDER

def change_permissions(folder):
    """Cambia los permisos de todos los archivos y carpetas dentro de 'folder'."""
    for root, dirs, files in os.walk(folder):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IWRITE)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IWRITE)

def delete_with_permissions(func, path, _):
    """Cambia permisos y elimina archivos protegidos."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_repo():
    """Clona el repositorio de GitHub y maneja permisos."""
    try:
        if os.path.exists(REPO_FOLDER):
            change_permissions(REPO_FOLDER)
            shutil.rmtree(REPO_FOLDER, onerror=delete_with_permissions)

        subprocess.run(["git", "clone", REPO_URL, REPO_FOLDER], check=True)
    except Exception as e:
        print(f"Error: {e}")
