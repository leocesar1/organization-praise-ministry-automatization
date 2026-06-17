# Praise Ministry Music Sync 🎵

Este projeto tem como objetivo automatizar o processo de backup e compartilhamento das trilhas (multitracks, renders, vozes e instrumentos) e mapas de arranjo do Ministério de Louvor. 

Ele varre uma pasta específica do OneDrive contendo os áudios e arquivos do Reaper (`.rpp`) e os publica automaticamente em Tópicos distintos no Telegram (um para arquivos de áudio e outro para mapas de arranjo), gerando um banco de dados inteligente para garantir consistência e evitar postagens duplicadas.

## Estrutura do Projeto

O projeto adota uma arquitetura limpa e modular:
- `core/`: Contém os modelos de dados, o parser de nomes de arquivos e o parser de arquivos `.rpp` Reaper.
- `services/`: Classes de integração com APIs externas (`OneDriveClient`, `TelegramBot`, `TelegramStorage`).
- `runners/`: Scripts executáveis (sincronizador de música, sincronizador de arranjos e utilitários).
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

### B) Telegram (`token`, `chat_id`, `message_thread_id`, `arrangement_topic_id`)
1. Crie um bot no [@BotFather](https://t.me/botfather) e copie o token para a propriedade correspondente no `credentials.json`.
2. Para descobrir o `chat_id` do seu grupo e o `message_thread_id` do seu tópico principal de músicas, rode o script utilitário abaixo:
   ```bash
   python get_telegram_ids.py
   ```
3. O bot agora publica mapas de arranjo em um tópico separado. Descubra o ID desse tópico e adicione em `arrangement_topic_id` nas configurações do Telegram.
4. Mande uma mensagem qualquer dentro do tópico desejado no Telegram e o terminal imprimirá os IDs para você copiar e colar.

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

### B) Sincronizador Principal (Sync Music + Arranjos)
Este é o script central que baixa do OneDrive e envia pro Telegram. 
Por padrão, ele realiza a sincronização dos áudios e **também do mapa de arranjo Reaper** (lendo o arquivo `.rpp` na raiz da pasta da música) vinculando a mensagem de áudio ao mapa por meio de um link na legenda.

```bash
# Modo Teste: Envia apenas 1 música (com mapa) e para
python -m runners.sync_music --test

# Modo de Lote: Processa até N músicas por vez
python -m runners.sync_music --limit 5

# Modo Completo: Sincroniza tudo
python -m runners.sync_music

# Sincroniza apenas os áudios (sem processar arquivos Reaper .rpp)
python -m runners.sync_music --no-arrangement
```

### C) Sincronizador de Arranjos (Sync Arrangements)
Runner focado exclusivamente na extração e publicação de mapas de arranjos a partir dos arquivos `.rpp`. Caso o áudio já esteja no Telegram, o script edita silenciosamente a mensagem original adicionando o link do mapa de arranjo.

```bash
# Executa a varredura normal de arranjos novos
python -m runners.sync_arrangements

# Força a re-postagem e re-leitura de todos os arquivos .rpp (editando mensagens existentes)
python -m runners.sync_arrangements --update

# Limita a execução no modo teste
python -m runners.sync_arrangements --test
```

### D) Limpeza do Canal (Cleanup)
Se você precisar resetar o seu banco de dados e apagar **todas** as mensagens do tópico de músicas do Telegram:
```bash
python -m runners.cleanup_telegram
```
*(Ele varre o canal inteiro, pede confirmação e apaga as mensagens, criando um terreno limpo).*

### E) Remoção Pontual (Remove from DB)
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

