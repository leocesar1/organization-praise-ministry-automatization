import json
import logging
from typing import Dict, Any
import requests
from services.onedrive import OneDriveClient

logger = logging.getLogger(__name__)

class OneDriveStorage:
    def __init__(self, onedrive: OneDriveClient, folder_id: str = "A9BCF86E0D3403C2!367937"):
        self.onedrive = onedrive
        self.folder_id = folder_id
        self._cache = None
        self.filename = "music_database.json"

    def load(self) -> dict:
        if self._cache is not None:
            return self._cache
            
        try:
            children = self.onedrive.get_folder_children(self.folder_id, filter_name=self.filename)
            
            # Find the exact match to avoid "music_database.json 1"
            exact_match = None
            for child in children:
                if child["name"] == f"{self.filename}.json" or child["name"] == self.filename:
                    exact_match = child
                    break
                    
            if not exact_match:
                # Se realmente não existir, retornamos vazio
                self._cache = {}
                return self._cache
                
            file_id = exact_match["id"]
            content = self.onedrive.download_file(file_id)
            self._cache = json.loads(content.decode("utf-8"))
        except Exception as e:
            logger.error(f"Erro fatal ao carregar {self.filename} do OneDrive: {e}")
            raise Exception(f"Falha ao carregar o banco de dados. Abortando para evitar sobrescrever dados: {e}")
            
        return self._cache

    def save(self, data: dict) -> None:
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1]['music_name'].lower()))
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        try:
            # Garante que o arquivo salvo tenha a extensão correta (.json) caso não esteja no self.filename
            save_name = f"{self.filename}.json" if not self.filename.endswith(".json") else self.filename
            url = f"{self.onedrive.base_url}/me/drive/items/{self.folder_id}:/{save_name}:/content"
            headers = self.onedrive.headers.copy()
            headers["Content-Type"] = "application/json; charset=utf-8"
            
            response = requests.put(url, headers=headers, data=json_content.encode("utf-8"))
            response.raise_for_status()
            logger.info(f"✅ {self.filename} salvo no OneDrive com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar {self.filename} no OneDrive: {e}")
            
        self._cache = sorted_data

    def is_synced(self, folder_id: str, music_name: str = None) -> bool:
        data = self.load()
        return folder_id in data

    def get_synced_info(self, folder_id: str, music_name: str = None) -> dict:
        data = self.load()
        return data.get(folder_id, {})

    def mark_synced(self, folder_id: str, message_id: int, metadata) -> None:
        data = self.load()
        existing = data.get(folder_id, {})
        data[folder_id] = {
            "message_id": message_id,
            "arrangement_txt_link": existing.get("arrangement_txt_link") or existing.get("arrangement_message_id"),
            "music_name": metadata.name,
            "artist": metadata.artist,
            "key": metadata.key,
            "bpm": metadata.bpm,
            "compass": metadata.compass,
            "elite": metadata.elite,
            "instrument": metadata.instrument,
            "status": "success"
        }
        self.save(data)

    def mark_arrangement_synced(self, folder_id: str, arrangement_txt_link: str, metadata=None) -> None:
        data = self.load()
        if folder_id in data:
            data[folder_id]["arrangement_txt_link"] = arrangement_txt_link
            if metadata:  # atualiza metadados se fornecidos
                data[folder_id]["music_name"] = metadata.name
                data[folder_id]["artist"] = metadata.artist
                data[folder_id]["key"] = metadata.key
                data[folder_id]["bpm"] = metadata.bpm
                data[folder_id]["compass"] = metadata.compass
                data[folder_id]["elite"] = metadata.elite
                data[folder_id]["instrument"] = metadata.instrument
        else:
            if metadata:
                data[folder_id] = {
                    "message_id": None,
                    "arrangement_txt_link": arrangement_txt_link,
                    "music_name": metadata.name,
                    "artist": metadata.artist,
                    "key": metadata.key,
                    "bpm": metadata.bpm,
                    "compass": metadata.compass,
                    "elite": metadata.elite,
                    "instrument": metadata.instrument,
                    "status": "success"
                }
            else:
                data[folder_id] = {
                    "message_id": None,
                    "arrangement_txt_link": arrangement_txt_link,
                    "music_name": "Desconhecido",
                    "status": "success"
                }
        self.save(data)

    def mark_error(self, folder_id: str, error_msg: str, metadata=None) -> None:
        data = self.load()
        existing = data.get(folder_id, {})
        entry = {
            "status": "error",
            "error": str(error_msg),
            "message_id": existing.get("message_id"),
            "arrangement_txt_link": existing.get("arrangement_txt_link") or existing.get("arrangement_message_id")
        }
        if metadata:
            entry["music_name"] = metadata.name
            entry["artist"] = metadata.artist
            entry["key"] = metadata.key
            entry["bpm"] = metadata.bpm
            entry["compass"] = metadata.compass
            entry["elite"] = metadata.elite
            entry["instrument"] = metadata.instrument
        else:
            entry["music_name"] = "Desconhecido (Falha no Parse)"
            
        data[folder_id] = entry
        self.save(data)

