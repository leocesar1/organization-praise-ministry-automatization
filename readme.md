# Praise Ministry Music Sync 🎵

Este projeto tem como objetivo automatizar o processo de backup e compartilhamento das trilhas (multitracks, renders, vozes e instrumentos) do Ministério de Louvor. 

Ele varre uma pasta específica do OneDrive contendo os áudios e os publica automaticamente em um Tópico no Telegram, gerando um banco de dados inteligente para garantir que nenhuma música seja postada duas vezes.

## Estrutura do Projeto

O projeto foi refatorado para usar uma arquitetura limpa e modular:
- `core/`: Contém os modelos de dados e a lógica de parser de nomes dos arquivos.
- `services/`: Classes de integração com APIs externas (`OneDriveClient`, `TelegramBot`, `TelegramStorage`).
- `runners/`: Scripts executáveis (o sincronizador principal e os utilitários).
- `default/`: Utilitários de leitura de credenciais.

## 1. Pré-requisitos e Instalação

1. Certifique-se de ter o Python 3 instalado.
2. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate  # no Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 2. Configurando o `credentials.json`

Crie um arquivo chamado `credentials.json` na raiz do projeto copiando a estrutura do `credentials MODEL.json`. 

### A) OneDrive (`client_id`)
1. Acesse o [Portal do Azure](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
2. Crie um "Novo registro" suportando contas pessoais da Microsoft (terceira opção).
3. Copie o **ID do aplicativo (cliente)** e cole em `onedrive.client_id`.
4. No menu "Autenticação" do Azure, vá em "Configurações Avançadas" e marque **"Permitir fluxos de cliente público"** como **SIM**. (Sem isso, o login via terminal não funcionará).

### B) Telegram (`token`, `chat_id`, `message_thread_id`)
1. Crie um bot no [@BotFather](https://t.me/botfather) e copie o token para a propriedade correspondente no `credentials.json`.
2. Para descobrir o `chat_id` do seu grupo e o `message_thread_id` do seu tópico, rode o script utilitário abaixo:
   ```bash
   python get_telegram_ids.py
   ```
3. Mande uma mensagem qualquer dentro do tópico desejado no Telegram e o terminal imprimirá os IDs para você copiar e colar.

> **Atenção:** O campo `storage_message_id` deve ficar em branco (`""`). Ele será preenchido automaticamente pelo script na primeira vez que rodar!

## 3. Scripts de Execução

Todos os scripts devem ser rodados a partir da raiz do projeto usando `python -m runners.<nome_do_script>`.

### A) Normalização do OneDrive (Obrigatório na 1ª vez)
Como o parser funciona detectando `" _ "` (espaço underline espaço), este script varre todo o OneDrive e converte antigos hífens (` - `) para underlines:
```bash
# Roda apenas em modo visualização (dry-run)
python -m runners.rename_onedrive

# Aplica a renomeação de fato
python -m runners.rename_onedrive --execute
```

### B) Sincronizador Principal (Sync)
Este é o script central que baixa do OneDrive e envia pro Telegram. 
Ao rodar pela primeira vez, ele exibirá um link no terminal para você autorizar o OneDrive pelo navegador.

```bash
# Modo Teste: Envia apenas 1 música e para (Ótimo para validar a autenticação)
python -m runners.sync_music --test

# Modo de Lote: Processa até N músicas por vez e para
python -m runners.sync_music --limit 5

# Modo Completo: Sincroniza todas as músicas faltantes
python -m runners.sync_music
```

### C) Limpeza do Canal (Cleanup)
Se você precisar resetar o seu banco de dados e apagar **todas** as mensagens do tópico de músicas do Telegram:
```bash
python -m runners.cleanup_telegram
```
*(Ele varre o canal inteiro, pede confirmação e apaga as mensagens, criando um terreno limpo).*

### D) Remoção Pontual (Remove from DB)
Se você quer forçar o re-envio de apenas **uma música específica**, você pode apagá-la do JSON do Telegram sem ter que editar o arquivo manualmente:
```bash
# Busca pelo nome e permite deletar do banco
python -m runners.remove_from_db "Nome da Música"
```

## Tratamento de Nomes Suportado

O sistema entende dois padrões principais de pastas e arquivos no OneDrive:
- Padrão A: `Nome [Elite] _ Tom _ Artista _ BPMbpm _ Compasso`
- Padrão B: `Instrumento _ Nome _ Tom _ Artista _ BPMbpm _ Compasso`

*(Onde a tag `[Elite]` é opcional).*
