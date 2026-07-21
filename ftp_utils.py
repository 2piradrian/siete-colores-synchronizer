import os
import shutil
import subprocess
import random
import string
import requests
from ftplib import FTP
from config import FTP_HOST, FTP_USER, FTP_PASSWORD, FTP_REMOTE_DIR, REPO_FOLDER, DOMAIN

def build_site():
    """Construye el sitio web utilizando npm."""
    try:
        use_shell = os.name == 'nt'
        subprocess.run(["npm", "i"], cwd=os.path.abspath(REPO_FOLDER), check=True, shell=use_shell)
        subprocess.run(["npm", "run", "build"], cwd=os.path.abspath(REPO_FOLDER), check=True, shell=use_shell)
    except Exception as e:
        print(f"Error en build_site: {e}")

def upload_to_ftp():
    """Sube el contenido de la carpeta 'public' al servidor FTP y extrae de forma remota."""
    public_folder = os.path.join(REPO_FOLDER, "public")

    # Nombres y tokens dinámicos
    secret_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    php_filename = "deploy_" + ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + ".php"

    zip_base_name = os.path.join(REPO_FOLDER, "build_deploy")
    zip_filename = "build_deploy.zip"
    zip_filepath = zip_base_name + ".zip"
    php_filepath = os.path.join(REPO_FOLDER, php_filename)

    try:
        # 1. Comprimir la carpeta public
        print("Comprimiendo la carpeta public a ZIP...")
        shutil.make_archive(zip_base_name, 'zip', public_folder)

        # 2. Crear el script PHP
        php_code = f"""<?php
        // Verificación de seguridad por token
        if (!isset($_POST['token']) || $_POST['token'] !== '{secret_token}') {{
            http_response_code(403);
            die('Acceso denegado.');
        }}

        // Extracción
        $zip = new ZipArchive;
        $res = $zip->open('{zip_filename}');
        if ($res === TRUE) {{
            $zip->extractTo('./');
            $zip->close();
            echo 'OK';
        }} else {{
            http_response_code(500);
            echo 'Error al descomprimir en el servidor.';
        }}

        // Autodestrucción
        @unlink('{zip_filename}');
        @unlink(__FILE__);
        ?>"""

        with open(php_filepath, "w") as f:
            f.write(php_code)

        # 3. Subir ZIP y PHP por FTP
        print("Subiendo ZIP y script de despliegue vía FTP...")
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASSWORD)
        ftp.cwd(FTP_REMOTE_DIR)

        with open(zip_filepath, 'rb') as f:
            ftp.storbinary(f'STOR {zip_filename}', f)

        with open(php_filepath, 'rb') as f:
            ftp.storbinary(f'STOR {php_filename}', f)

        ftp.quit()
        print("Archivos subidos. Iniciando descompresión remota HTTP...")

        # 4. Ejecutar la extracción vía HTTP mediante POST
        deploy_url = f"{DOMAIN}/{php_filename}"
        response = requests.post(deploy_url, data={'token': secret_token}, timeout=60)

        if response.status_code == 200 and response.text.strip() == "OK":
            print("¡Despliegue completado con éxito!")
        else:
            print(f"Error en el despliegue HTTP {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Error general en upload_to_ftp: {e}")

    finally:
        # 5. Limpieza local (borra el ZIP y el PHP de tu máquina)
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
        if os.path.exists(php_filepath):
            os.remove(php_filepath)
