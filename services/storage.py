import json
import logging
import os
from typing import Dict, Any
from services.telegram import TelegramBot
from default.default import get_Credentials

logger = logging.getLogger(__name__)

class TelegramStorage:
    def __init__(self, bot: TelegramBot):
        self._bot = bot
        self._cache = None
        
        creds = get_Credentials("telegram")["telegram"]
        # Precisamos de um storage_topic_id (pode ser o mesmo de mensagens ou outro)
        self.topic_id = creds.get("storage_topic_id", creds.get("message_thread_id"))
        self.storage_message_id = creds.get("storage_message_id")

    def _update_credentials_file(self):
        try:
            cred_path = "credentials.json"
            if os.path.exists(cred_path):
                with open(cred_path, "r") as f:
                    creds = json.load(f)
                
                if "telegram" not in creds:
                    creds["telegram"] = {}
                creds["telegram"]["storage_message_id"] = self.storage_message_id
                
                with open(cred_path, "w") as f:
                    json.dump(creds, f, indent=4)
                logger.info(f"✅ credentials.json atualizado automaticamente com o novo storage_message_id: {self.storage_message_id}")
        except Exception as e:
            logger.error(f"Não foi possível atualizar credentials.json: {e}")

    def _get_document_file_id(self) -> str:
        """Workaround para pegar o file_id de uma mensagem existente: encaminha para o próprio chat."""
        try:
            forwarded = self._bot.bot.forward_message(
                chat_id=self._bot.chat_id,
                from_chat_id=self._bot.chat_id,
                message_id=self.storage_message_id,
                message_thread_id=self.topic_id
            )
            file_id = forwarded.document.file_id
            self._bot.delete_message(forwarded.message_id)
            return file_id
        except Exception as e:
            logger.error(f"Erro ao recuperar mensagem de storage: {e}")
            return None

    def load(self) -> dict:
        if self._cache is not None:
            return self._cache
            
        if not self.storage_message_id:
            logger.warning("storage_message_id não configurado. Criando novo dicionário vazio.")
            self._cache = {}
            # Inicializa uma mensagem vazia
            self.save(self._cache)
            logger.info(f"Por favor, salve este ID no credentials.json como 'storage_message_id': {self.storage_message_id}")
            return self._cache

        file_id = self._get_document_file_id()
        if not file_id:
            logger.warning("Não foi possível ler o storage do Telegram. Retornando vazio.")
            self._cache = {}
            return self._cache

        content = self._bot.get_document_content(file_id)
        try:
            self._cache = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("JSON inválido no storage do Telegram. Criando novo.")
            self._cache = {}
            
        return self._cache

    def save(self, data: dict) -> None:
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1]['music_name'].lower()))
        json_content = json.dumps(sorted_data, indent=4, ensure_ascii=False)
        
        if not self.storage_message_id:
            msg_id = self._bot.send_document("music_database.json", json_content, self.topic_id)
            self.storage_message_id = msg_id
            self._update_credentials_file()
            logger.info(f"Novo storage criado. message_id: {msg_id}")
        else:
            try:
                self._bot.edit_document(self.storage_message_id, "music_database.json", json_content)
            except Exception as e:
                logger.error(f"Erro ao atualizar storage (edit): {e}. Enviando novo.")
                msg_id = self._bot.send_document("music_database.json", json_content, self.topic_id)
                self.storage_message_id = msg_id
                self._update_credentials_file()
                logger.info(f"Novo storage criado no fallback. Atualize o ID para: {msg_id}")
                
        self._cache = sorted_data

    def is_synced(self, folder_id: str) -> bool:
        data = self.load()
        return folder_id in data

    def mark_synced(self, folder_id: str, message_id: int, metadata) -> None:
        data = self.load()
        existing = data.get(folder_id, {})
        data[folder_id] = {
            "message_id": message_id,
            "arrangement_message_id": existing.get("arrangement_message_id"),
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

    def mark_arrangement_synced(self, folder_id: str, arrangement_message_id: int, metadata=None) -> None:
        data = self.load()
        if folder_id in data:
            data[folder_id]["arrangement_message_id"] = arrangement_message_id
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
                    "arrangement_message_id": arrangement_message_id,
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
                    "arrangement_message_id": arrangement_message_id,
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
            "arrangement_message_id": existing.get("arrangement_message_id")
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

