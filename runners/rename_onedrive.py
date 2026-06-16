import argparse
import logging
import re
from tqdm import tqdm
from services.onedrive import OneDriveClient

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def normalize_name(name: str) -> str:
    """Substitui ' - ' por ' _ ', preservando hífens internos."""
    # Usando replace simples para garantir que a correspondência de espaço + hífen + espaço seja exata
    return name.replace(" - ", " _ ")

def rename_all(onedrive: OneDriveClient, path_id: str = "A9BCF86E0D3403C2!367937", dry_run: bool = True):
    logger.info(f"Listando arquivos na pasta id: {path_id}...")
    items = onedrive.get_file_list(path_id)
    
    for item in items:
        name = item["name"]
        item_id = item["id"]
        
        # Passo 1: Se for diretório, faz a chamada recursiva PRIMEIRO para renomear os arquivos internos
        if "folder" in item:
            rename_all(onedrive, item_id, dry_run=dry_run)
            
        # Passo 2: Renomeia o item atual (seja ele arquivo ou o diretório que acabamos de visitar)
        new_name = normalize_name(name)
        if new_name != name:
            if dry_run:
                logger.info(f"[DRY-RUN] '{name}' -> '{new_name}'")
            else:
                try:
                    onedrive.rename_item(item_id, new_name)
                    logger.info(f"[OK] '{name}' -> '{new_name}'")
                except Exception as e:
                    logger.error(f"[ERRO] Falha ao renomear '{name}': {e}")
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renomeia ' - ' para ' _ ' no OneDrive.")
    parser.add_argument("--execute", action="store_true", help="Executa a renomeação (sem isso, roda em dry-run)")
    parser.add_argument("--folder", type=str, default="A9BCF86E0D3403C2!367937", help="ID da pasta principal")
    args = parser.parse_args()
    
    onedrive = OneDriveClient()
    onedrive.authenticate()
    
    dry_run = not args.execute
    if dry_run:
        logger.info("=== MODO DRY-RUN (adicione --execute para aplicar) ===")
        
    rename_all(onedrive, args.folder, dry_run=dry_run)
