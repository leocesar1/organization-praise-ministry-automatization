import logging
from services.telegram import TelegramBot
import telebot

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def test_delete_message(msg_id: int):
    bot = TelegramBot()
    logger.info(f"Tentando deletar a mensagem com ID: {msg_id} no chat: {bot.chat_id}")
    
    try:
        # Acessamos a biblioteca do bot diretamente para pegar o erro cru sem filtros
        result = bot.bot.delete_message(chat_id=bot.chat_id, message_id=msg_id)
        if result:
            logger.info(f"✅ SUCESSO! A mensagem {msg_id} foi apagada com sucesso.")
        else:
            logger.info(f"❌ A API retornou False para a deleção da mensagem {msg_id}.")
            
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"❌ ERRO DA API DO TELEGRAM ao deletar: {e.description}")
    except Exception as e:
        logger.error(f"❌ ERRO DESCONHECIDO: {e}")

if __name__ == "__main__":
    # Testando o ID que o usuário mandou: 4208
    test_delete_message(4208)
