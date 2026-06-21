import os
import msal
import requests
import logging
from typing import List, Dict, Any
from default.default import get_Credentials

logger = logging.getLogger(__name__)

class OneDriveClient:
    def __init__(self):
        creds = get_Credentials("onedrive")["onedrive"]
        self.client_id = creds["client_id"]
        # tenant id is typically 'common' for personal/multi-tenant accounts
        self.authority = "https://login.microsoftonline.com/common"
        self.scopes = ["Files.ReadWrite"]
        self.token_cache = msal.SerializableTokenCache()
        self.cache_file = "onedrive_token.json"
        
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.token_cache.deserialize(f.read())
                
        self.app = msal.PublicClientApplication(
            self.client_id, authority=self.authority,
            token_cache=self.token_cache
        )
        self.access_token = None
        self.base_url = "https://graph.microsoft.com/v1.0"

    def authenticate(self) -> None:
        """Authenticate using Device Code Flow if needed."""
        accounts = self.app.get_accounts()
        result = None
        
        if accounts:
            logger.info("Tentando usar token cacheado...")
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            
        if not result:
            logger.info("Nenhum token válido encontrado. Iniciando Device Code Flow...")
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            if "user_code" not in flow:
                raise ValueError("Falha ao iniciar Device Flow: %s" % flow)
                
            print(flow["message"])
            result = self.app.acquire_token_by_device_flow(flow)
            
        if "access_token" in result:
            self.access_token = result["access_token"]
            with open(self.cache_file, "w") as f:
                f.write(self.token_cache.serialize())
            logger.info("✅ OneDrive autenticado com sucesso.")
        else:
            raise Exception("Falha na autenticação: " + str(result.get("error_description", result)))

    @property
    def headers(self) -> Dict[str, str]:
        if not self.access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_file_list(self, path_id: str = "A9BCF86E0D3403C2!367937") -> List[Dict[str, Any]]:
        """List all items in the given folder."""
        url = f"{self.base_url}/me/drive/items/{path_id}/children"
        result = []
        
        while url:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            result.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            
        return result

    def get_folder_children(self, folder_id: str, filter_name: str = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/me/drive/items/{folder_id}/children"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        children = response.json().get("value", [])
        
        if filter_name:
            children = [c for c in children if c.get("name") == filter_name]
            
        return children

    def download_file(self, file_id: str) -> bytes:
        """Download file content by its ID."""
        url = f"{self.base_url}/me/drive/items/{file_id}/content"
        response = requests.get(url, headers=self.headers, allow_redirects=True)
        response.raise_for_status()
        return response.content

    def get_renders(self, folder_id: str) -> Dict[str, bytes]:
        """Extrai os arquivos de render da pasta '1 _ Renders'."""
        subfolders = self.get_folder_children(folder_id, filter_name="1 _ Renders")
        if not subfolders:
            raise FileNotFoundError(f"Pasta '1 _ Renders' não encontrada no id {folder_id}")
            
        renders_folder_id = subfolders[0]["id"]
        files = self.get_folder_children(renders_folder_id)
        
        downloaded = {}
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            file_size = file.get("size", 0)
            
            # Limite do Telegram Bot API é 50MB (usaremos 49.5MB por segurança)
            if file_size > 49.5 * 1024 * 1024:
                logger.warning(f"⚠️ O arquivo {file_name} excede o limite de 50MB do Telegram (Tamanho: {file_size / 1024 / 1024:.2f}MB). Pulando...")
                continue
                
            logger.info(f"Baixando {file_name}...")
            content = self.download_file(file_id)
            downloaded[file_name] = content
            
        return downloaded

    def get_rpp_file(self, folder_id: str) -> tuple[str, bytes] | tuple[None, None]:
        """Busca o arquivo .rpp no diretório pai da pasta '1 _ Renders' (folder_id)."""
        files = self.get_folder_children(folder_id)
        for file in files:
            file_name = file["name"]
            if file_name.lower().endswith(".rpp"):
                logger.info(f"Encontrado arquivo Reaper: {file_name}. Baixando...")
                content = self.download_file(file["id"])
                return file_name, content
        return None, None

    def rename_item(self, item_id: str, new_name: str) -> None:
        """Rename an item in OneDrive."""
        url = f"{self.base_url}/me/drive/items/{item_id}"
        payload = {"name": new_name}
        response = requests.patch(url, headers=self.headers, json=payload)
        response.raise_for_status()

    def get_or_create_folder(self, folder_name: str, parent_id: str = "A9BCF86E0D3403C2!367937") -> str:
        """Obtém o ID da pasta, ou a cria se não existir."""
        children = self.get_folder_children(parent_id, filter_name=folder_name)
        if children:
            return children[0]["id"]
            
        # Criar a pasta
        url = f"{self.base_url}/me/drive/items/{parent_id}/children"
        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()["id"]

    def upload_txt_file(self, filename: str, content: str, parent_id: str = "A9BCF86E0D3403C2!367937") -> str:
        """
        Faz upload de um arquivo .txt e retorna o webUrl do item.
        """
        folder_id = self.get_or_create_folder("mapas", parent_id=parent_id)
        
        url = f"{self.base_url}/me/drive/items/{folder_id}:/{filename}:/content"
        headers = self.headers.copy()
        headers["Content-Type"] = "text/plain; charset=utf-8"
        
        response = requests.put(url, headers=headers, data=content.encode("utf-8"))
        response.raise_for_status()
        
        data = response.json()
        return data.get("webUrl", "")

    def upload_json_file(self, filename: str, content: str, parent_id: str = "A9BCF86E0D3403C2!367937") -> str:
        """
        Faz upload de um arquivo .json e retorna o webUrl do item.
        """
        folder_id = self.get_or_create_folder("mapas", parent_id=parent_id)
        
        url = f"{self.base_url}/me/drive/items/{folder_id}:/{filename}:/content"
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json; charset=utf-8"
        
        response = requests.put(url, headers=headers, data=content.encode("utf-8"))
        response.raise_for_status()
        
        data = response.json()
        return data.get("webUrl", "")

