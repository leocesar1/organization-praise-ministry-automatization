import telebot
from default.default import get_Credentials

print("Iniciando bot para capturar IDs...")
try:
    # Tenta pegar o token do credentials.json se já estiver lá
    token = get_Credentials("telegram")["telegram"]["token"]["praiseMinistryBot"]
    if not token or token == "<YOUR_BOT_TOKEN>":
        raise ValueError()
except:
    # Se não estiver no arquivo, pede para o usuário colar
    token = input("Cole o TOKEN do seu Bot (pegue no @BotFather): ")

bot = telebot.TeleBot(token)

print("\nBot online! 🟢")
print("Vá até o Telegram, adicione o bot no seu Grupo (se ainda não adicionou).")
print("Em seguida, mande uma mensagem (ex: 'teste') dentro do Tópico que você quer usar para as músicas.")
print("Aguardando mensagem...\n")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    print("=" * 40)
    print("✅ MENSAGEM RECEBIDA!")
    print(f"Texto: {message.text}")
    print(f"Chat ID (Seu Grupo): {message.chat.id}")
    
    if message.message_thread_id:
        print(f"Message Thread ID (Tópico): {message.message_thread_id}")
    else:
        print("Message Thread ID: (Nenhum - Esta mensagem não foi enviada em um tópico)")
        
    print("=" * 40)
    print("\nCopie os IDs acima e cole no seu credentials.json!")
    print("Você pode apertar Ctrl+C para encerrar agora.")

bot.polling()
