import telebot
import logging
from typing import Dict, List
from core.models import MusicMetadata
from default.default import get_Credentials

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token=None):
        self.getDefaultsValues = get_Credentials("telegram")["telegram"]
        self.token = token if token is not None else self.getDefaultsValues["token"]["praiseMinistryBot"]
        self.bot = telebot.TeleBot(self.token, parse_mode="MarkdownV2", num_threads=1)
        self.chat_id = self.getDefaultsValues["chat_id"]
        self.topic_id = self.getDefaultsValues["message_thread_id"]
        self.arrangement_topic_id = self.getDefaultsValues.get("arrangement_topic_id", self.topic_id)

    def escape_markdown(self, text: str) -> str:
        """Escapes markdown v2 reserved characters."""
        if not text:
            return ""
        # Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(char, f'\\{char}')
        return text

    def make_caption(self, metadata: MusicMetadata, arrangement_message_id: int = None) -> str:
        caption = f"🎶 Música: *{self.escape_markdown(metadata.name)}*\n"
        caption += f"🎤 Intérprete: *{self.escape_markdown(metadata.artist)}*\n"
        caption += f"🎼 Tom Original: *{self.escape_markdown(metadata.key)}*\n"
        
        bpm_text = f"{metadata.bpm} BPM" if metadata.bpm > 0 else "0 BPM"
        caption += f"⏳ Andamento: *{self.escape_markdown(bpm_text)} — {self.escape_markdown(metadata.compass)}*\n"
        
        if metadata.elite:
            caption += f"🏆 Elite: ✅\n"
            
        if metadata.instrument:
            caption += f"🎸 Instrumento: *{self.escape_markdown(metadata.instrument)}*\n"
            
        if arrangement_message_id:
            chat_clean = str(self.chat_id).replace("-100", "")
            link = f"https://t.me/c/{chat_clean}/{arrangement_message_id}"
            caption += f"\n📋 *[Ver Mapa de Arranjo]({link})*\n"
            
        return caption

    def make_input_media_audio(self, filename: str, content: bytes, caption: str = None, metadata: MusicMetadata = None):
        from core.name_parser import parse_music_metadata
        clean_filename = filename.replace(".mp3", "").replace(".wav", "").replace(".m4a", "")
        file_meta = parse_music_metadata(clean_filename)
        
        # O título será o nome da música + instrumento se houver, senão o nome da música original
        if file_meta.instrument:
            title = f"{metadata.name} - {file_meta.instrument.capitalize()}"
        else:
            title = metadata.name
        
        return telebot.types.InputMediaAudio(
            media=content,
            title=title,
            caption=caption,
            performer=metadata.artist if metadata else None,
            parse_mode="MarkdownV2"
        )

    def send_audio_group(self, metadata: MusicMetadata, files: Dict[str, bytes], arrangement_message_id: int = None) -> int:
        """Sends a group of audio files and returns the message ID of the first message."""
        if not files:
            raise ValueError("Nenhum arquivo para enviar")
            
        audio_medias = []
        is_first = True
        
        for filename, content in files.items():
            caption = self.make_caption(metadata, arrangement_message_id) if is_first else None
            
            # Construir nome de arquivo completo para carregamento individual
            complete_filename = f"{metadata.name} - {filename}"
            media_content = (complete_filename, content)
            
            media = self.make_input_media_audio(filename, media_content, caption=caption, metadata=metadata)
            audio_medias.append(media)
            is_first = False
            
        # O telegram tem limite de 10 mídias por group. Se houver mais, precisa paginar.
        # Mas vamos assumir que são < 10 para o caso de uso.
        if len(audio_medias) > 10:
            logger.warning("Mais de 10 arquivos. Enviando apenas os 10 primeiros no mesmo grupo.")
            audio_medias = audio_medias[:10]
            
        try:
            result = self.bot.send_media_group(
                self.chat_id, 
                media=audio_medias, 
                timeout=900, 
                message_thread_id=self.topic_id
            )
            return result[0].message_id
        except Exception as e:
            logger.error(f"Erro ao enviar media group, tentando individual: {e}")
            first_msg_id = None
            for i, media in enumerate(audio_medias):
                res = self.bot.send_audio(
                    self.chat_id,
                    audio=media.media,
                    caption=media.caption,
                    title=media.title,
                    performer=media.performer,
                    parse_mode="MarkdownV2",
                    message_thread_id=self.topic_id,
                    timeout=900
                )
                if i == 0:
                    first_msg_id = res.message_id
            return first_msg_id

    def send_document(self, filename: str, content: str, message_thread_id: int) -> int:
        """Sends a document and returns the message_id."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        with open(filename, "rb") as f:
            msg = self.bot.send_document(
                self.chat_id,
                document=f,
                message_thread_id=message_thread_id
            )
        import os
        os.remove(filename)
        return msg.message_id

    def edit_document(self, message_id: int, filename: str, content: str) -> None:
        """Edits an existing document message."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        with open(filename, "rb") as f:
            media = telebot.types.InputMediaDocument(f)
            self.bot.edit_message_media(
                chat_id=self.chat_id,
                message_id=message_id,
                media=media
            )
        import os
        os.remove(filename)

    def send_text_message(self, text: str, message_thread_id: int) -> int:
        """Sends a text message and returns the message_id."""
        msg = self.bot.send_message(
            self.chat_id,
            text,
            parse_mode="MarkdownV2",
            message_thread_id=message_thread_id
        )
        return msg.message_id

    def edit_text_message(self, message_id: int, text: str) -> None:
        """Edits an existing text message."""
        self.bot.edit_message_text(
            text,
            chat_id=self.chat_id,
            message_id=message_id,
            parse_mode="MarkdownV2"
        )

    def edit_message_caption(self, message_id: int, caption: str) -> None:
        """Edits the caption of an existing message (like the first audio in a media group)."""
        self.bot.edit_message_caption(
            chat_id=self.chat_id,
            message_id=message_id,
            caption=caption,
            parse_mode="MarkdownV2"
        )

    def get_document_content(self, file_id: str) -> bytes:
        """Downloads a document from Telegram."""
        file_info = self.bot.get_file(file_id)
        downloaded_file = self.bot.download_file(file_info.file_path)
        return downloaded_file

    def get_message(self, message_id: int):
        # We can't directly get a message content by ID via standard API easily without storing it or forwarding
        pass

    def delete_message(self, message_id: int) -> bool:
        try:
            return self.bot.delete_message(chat_id=self.chat_id, message_id=message_id)
        except telebot.apihelper.ApiTelegramException as e:
            if "message to delete not found" in str(e) or "message can't be deleted" in str(e):
                return False
            logger.error(f"Erro ao deletar msg {message_id}: {e}")
            raise
