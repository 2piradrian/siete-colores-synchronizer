from git_utils import clone_repo
from db_utils import connect_to_mongo, export_collections
from image_utils import copy_and_convert_images
from ftp_utils import build_site, upload_to_ftp

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