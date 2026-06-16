import argparse
import logging
import time
from tqdm import tqdm
from services.telegram import TelegramBot

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def cleanup_music_topic(bot: TelegramBot, from_id: int = None, to_id: int = None):
    if from_id is None or to_id is None:
        logger.info("IDs não informados. Descobrindo o limite enviando uma mensagem temporária...")
        try:
            # Envia uma mensagem pra pegar o ID mais alto
            # Usando uma string simples sem caracteres especiais do MarkdownV2 (como o ponto)
            msg = bot.bot.send_message(bot.chat_id, "Buscando IDs", message_thread_id=bot.topic_id)
            to_id = msg.message_id
            bot.delete_message(to_id)
            from_id = 1
        except Exception as e:
            logger.error(f"Erro ao tentar descobrir os IDs: {e}")
            return
            
    logger.warning(f"⚠️ AVISO: Isso tentará apagar todas as mensagens no range {from_id} até {to_id}.")
    logger.warning("Essa ação é IRREVERSÍVEL.")
    
    confirm = input("Tem certeza que deseja continuar? (digite 'SIM' para confirmar): ")
    if confirm != "SIM":
        logger.info("Operação cancelada.")
        return
        
    deleted = 0
    errors = 0
    
    for msg_id in tqdm(range(to_id, from_id - 1, -1), desc="Apagando mensagens (da mais nova para a mais antiga)"):
        try:
            success = bot.delete_message(msg_id)
            if success:
                deleted += 1
            time.sleep(0.05)  # Rate limiting básico
        except Exception as e:
            errors += 1
            
    logger.info(f"\nConcluído!")
    logger.info(f"Mensagens apagadas: {deleted}")
    logger.info(f"Erros (provavelmente já apagadas ou não existem): {errors}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apaga todas as mensagens do Tópico indicado nas configurações do Telegram.")
    parser.add_argument("--from-id", type=int, help="ID inicial opcional")
    parser.add_argument("--to-id", type=int, help="ID final opcional")
    args = parser.parse_args()
    
    bot = TelegramBot()
    cleanup_music_topic(bot, args.from_id, args.to_id)
