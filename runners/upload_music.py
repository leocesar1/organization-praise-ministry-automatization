import os
import sys
import argparse
import logging
from services.onedrive import OneDriveClient

# Garante que os logs saiam em stderr para o stdout ficar limpo para o ID retornado
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)

# Arquivos ou pastas de sistema a serem ignorados no upload
IGNORED_NAMES = {".DS_Store", "Thumbs.db", ".git", ".idea"}

def upload_folder_recursive(onedrive: OneDriveClient, local_dir: str, target_parent_id: str):
    """Envia recursivamente todos os arquivos e subpastas de local_dir para a pasta target_parent_id no OneDrive."""
    items = sorted(os.listdir(local_dir))

    for item_name in items:
        if item_name in IGNORED_NAMES or item_name.startswith("._"):
            continue

        item_path = os.path.join(local_dir, item_name)

        if os.path.isdir(item_path):
            logger.info(f"📁 Criando/acessando subpasta remota: {item_name}")
            subfolder_id = onedrive.get_or_create_folder(item_name, parent_id=target_parent_id)
            upload_folder_recursive(onedrive, item_path, subfolder_id)
        elif os.path.isfile(item_path):
            file_size_mb = os.path.getsize(item_path) / (1024 * 1024)
            logger.info(f"⬆️  Enviando arquivo: {item_name} ({file_size_mb:.2f} MB)...")
            with open(item_path, "rb") as f:
                content = f.read()
            onedrive.upload_file(item_name, content, folder_id=target_parent_id)

def main():
    parser = argparse.ArgumentParser(description="Faz upload de uma pasta local para a raiz de músicas do OneDrive.")
    parser.add_argument("--local-path", type=str, required=True, help="Caminho completo da pasta local a ser enviada")
    parser.add_argument("--root-parent-id", type=str, default="A9BCF86E0D3403C2!367937", help="ID da pasta raiz de músicas no OneDrive")
    args = parser.parse_args()

    local_path = os.path.abspath(os.path.expanduser(args.local_path))
    if not os.path.isdir(local_path):
        logger.error(f"O caminho local não é uma pasta válida: {local_path}")
        sys.exit(1)

    folder_name = os.path.basename(local_path.rstrip(os.sep))
    logger.info(f"Iniciando upload da pasta '{folder_name}' para o OneDrive...")

    onedrive = OneDriveClient()
    onedrive.authenticate()

    # 1. Cria ou obtém a pasta principal no OneDrive (junto com as demais músicas)
    remote_folder_id = onedrive.get_or_create_folder(folder_name, parent_id=args.root_parent_id)
    logger.info(f"Pasta remota pronta no OneDrive (ID: {remote_folder_id}).")

    # 2. Faz o upload recursivo de todo o conteúdo da pasta
    upload_folder_recursive(onedrive, local_path, remote_folder_id)
    logger.info(f"✅ Todos os arquivos da pasta '{folder_name}' foram enviados com sucesso ao OneDrive!")

    # Imprime o ID da pasta remota na saída padrão para ser capturado por scripts
    print(remote_folder_id)

if __name__ == "__main__":
    main()
