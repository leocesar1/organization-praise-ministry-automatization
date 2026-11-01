import os
import sys
import argparse
import logging
from tqdm import tqdm
from services.onedrive import OneDriveClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def download_folder_recursive(onedrive: OneDriveClient, folder_id: str, local_path: str):
    """Baixa recursivamente todo o conteúdo de uma pasta do OneDrive preservando a estrutura local."""
    os.makedirs(local_path, exist_ok=True)
    items = onedrive.get_folder_children(folder_id)

    for item in items:
        item_id = item["id"]
        item_name = item["name"]
        item_local_path = os.path.join(local_path, item_name)

        if "folder" in item:
            # É uma subpasta: chama recursivamente
            logger.info(f"📁 Entrando na subpasta: {item_name}")
            download_folder_recursive(onedrive, item_id, item_local_path)
        else:
            # É um arquivo
            size_mb = item.get("size", 0) / (1024 * 1024)
            logger.info(f"⬇️  Baixando: {item_name} ({size_mb:.2f} MB)...")
            content = onedrive.download_file(item_id)
            with open(item_local_path, "wb") as f:
                f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Baixa uma pasta completa de música do OneDrive.")
    parser.add_argument("--folder-id", type=str, required=True, help="ID da pasta no OneDrive")
    parser.add_argument("--dest-dir", type=str, default=os.path.expanduser("~/Downloads"), help="Diretório de destino")
    args = parser.parse_args()

    onedrive = OneDriveClient()
    onedrive.authenticate()

    logger.info(f"Obtendo informações da pasta {args.folder_id}...")
    folder_info = onedrive.get_item(args.folder_id)
    folder_name = folder_info.get("name", "Musica_Download")

    destination_folder = os.path.join(args.dest_dir, folder_name)
    logger.info(f"Destino local: {destination_folder}")

    download_folder_recursive(onedrive, args.folder_id, destination_folder)
    logger.info(f"✅ Download concluído com sucesso em: {destination_folder}")

    # Imprime o caminho final na saída padrão para ser capturado por scripts
    print(destination_folder)

if __name__ == "__main__":
    main()
