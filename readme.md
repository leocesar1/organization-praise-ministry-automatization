# Praise Ministry Music Sync 🎵

Este projeto tem como objetivo automatizar o processo de backup e compartilhamento das trilhas (multitracks, renders, vozes e instrumentos) e mapas de arranjo do Ministério de Louvor. 

Ele varre uma pasta específica do OneDrive contendo os áudios e arquivos do Reaper (`.rpp`), enviando os áudios para um Tópico no Telegram e fazendo upload dos mapas harmônicos no OneDrive, vinculando-os automaticamente na legenda da mensagem da música com a estrutura de seções (Introdução, Verso, Refrão, etc.) e o link para o mapa completo. Isso gera um banco de dados inteligente para garantir consistência e evitar postagens duplicadas.

## Estrutura do Projeto

O projeto adota uma arquitetura limpa e modular:
- `core/`: Contém os modelos de dados, o parser de nomes de arquivos e o parser de arquivos `.rpp` Reaper.
- `services/`: Classes de integração com APIs externas (`OneDriveClient`, `TelegramBot`, `OneDriveStorage`, `AudioCompressor`).
- `runners/`: Scripts executáveis (sincronizador de música, sincronizador de arranjos e utilitários).
- `default/`: Utilitários de leitura de credenciais.

## 1. Pré-requisitos e Instalação

1. Certifique-se de ter o **Python 3** e o **ffmpeg** instalados:
   ```bash
   # macOS (via Homebrew)
   brew install ffmpeg
   ```
2. Crie um ambiente virtual e instale as dependências Python:
   ```bash
   python -m venv venv
   source venv/bin/activate  # no Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

> **Nota:** O `ffmpeg` é necessário para a compressão automática de áudios grandes antes do envio ao Telegram.

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

### B) Sincronizador Principal (Sync Music + Arranjos)
Este é o script central que baixa do OneDrive e envia pro Telegram. 
Por padrão, ele realiza a sincronização dos áudios e **também do mapa de arranjo Reaper** (lendo o arquivo `.rpp` na raiz da pasta da música) vinculando a mensagem de áudio ao mapa por meio da **estrutura de seções com timestamps** e de um link para o mapa completo na legenda.

```bash
# Modo Teste: Envia apenas 1 música (com mapa) e para
python -m runners.sync_music --test

# Modo de Lote: Processa até N músicas por vez
python -m runners.sync_music --limit 5

# Modo Completo: Sincroniza tudo
python -m runners.sync_music

# Sincroniza apenas os áudios (sem processar arquivos Reaper .rpp)
python -m runners.sync_music --no-arrangement

# Sincroniza apenas uma pasta específica
python -m runners.sync_music --folder "Nome da Música"
```

### C) Sincronizador de Arranjos (Sync Arrangements)
Runner focado exclusivamente na extração e publicação de mapas de arranjos a partir dos arquivos `.rpp`. Caso o áudio já esteja no Telegram, o script edita silenciosamente a mensagem original adicionando a estrutura de seções e o link do mapa de arranjo.

```bash
# Executa a varredura normal de arranjos novos
python -m runners.sync_arrangements

# Força a re-postagem e re-leitura de todos os arquivos .rpp (editando mensagens existentes)
python -m runners.sync_arrangements --update

# Sincroniza apenas uma pasta específica (pode ser combinado com --update)
python -m runners.sync_arrangements --folder "Nome da Música"

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

### F) Fluxo Inverso de Cifras (TXT → RPP)
Esta feature permite que o usuário edite o arquivo de texto (`.txt`) exportado com o mapa harmônico no OneDrive e, com um único comando, atualize o arquivo `.rpp` correspondente. O script cria uma trilha MIDI chamada "Cifras" no final do arquivo Reaper contendo os acordes mapeados em suas posições corretas de tempo e compasso. 
Suporta a leitura de graus relativos e também de cifras absolutas.

Para executar o script informando a pasta da música no OneDrive:
```bash
python -m runners.txt_to_rpp --folder "Bom perfume _ G _ Gabi Sampaio _ 71BPM _ 4.4"
```

O script localizará a música no OneDrive, lerá o `.txt` editado na subpasta `Mapas`, e fará a injeção ou substituição inteligente do bloco `<ITEM>` MIDI na faixa `Cifras` preservando as demais configurações da track. Em seguida, fará o **upload automático e sobrescreverá** o `.rpp` original na nuvem.

> **Nota:** Caso queira gerar um arquivo local para testes sem afetar o projeto na nuvem, você pode passar a flag `--output`:
> `python -m runners.txt_to_rpp --folder "Nome da Pasta" --output "meu_teste.rpp"`

## Tratamento de Nomes Suportado

O sistema entende dois padrões principais de pastas e arquivos no OneDrive:
- Padrão A: `Nome [Elite] _ Tom _ Artista _ BPMbpm _ Compasso`
- Padrão B: `Instrumento _ Nome _ Tom _ Artista _ BPMbpm _ Compasso`

*(Onde a tag `[Elite]` é opcional).*

## 🗜️ Compressão Automática de Áudio

Antes de enviar os arquivos ao Telegram, o sistema verifica automaticamente se o **tamanho total dos áudios** de uma música ultrapassa **48 MB** (limite seguro da API do Telegram).

Se o limite for excedido, o módulo `services/audio_compressor.py` recomprime todos os arquivos progressivamente usando o `ffmpeg`, reduzindo o bitrate em etapas até caber no limite:

| Tentativa | Bitrate |
|-----------|---------|
| 1ª        | 128 kbps |
| 2ª        | 96 kbps  |
| 3ª        | 64 kbps  |
| 4ª        | 48 kbps  |

O envio é **sempre realizado como media group** (grupo único no Telegram), nunca de forma individual. Se nem com 48 kbps for possível atingir o limite, o sistema envia com o menor bitrate disponível e registra um aviso nos logs.

## 🎼 Legenda da Mensagem de Áudio

Cada mensagem de áudio enviada ao Telegram inclui na legenda:

```
🎶 Música: Nome da Música
🎤 Intérprete: Artista
🎼 Tom Original: Gb
⏳ Andamento: 136 BPM — 4/4

📋 Estrutura / Arranjo:
00:00 Contagem
00:05 Introdução
00:18 Verso 1
00:46 Refrão
01:14 Verso 2
...

📋 Baixar Mapa Harmônico
```

A estrutura de seções com timestamps é extraída diretamente das **regiões do arquivo `.rpp`** do Reaper. Quando o arranjo é sincronizado posteriormente via `sync_arrangements`, a legenda da mensagem original é editada automaticamente para incluir a estrutura.

## 🎼 Extração de Cifras e Acordes (Reaper `.rpp`)

O sincronizador possui suporte para ler arquivos `.rpp` do Reaper e gerar um mapa visual de cifras debaixo de cada região correspondente:
1. **Identificação da Faixa:** O parser prioriza uma faixa MIDI nomeada como `"Cifras"` ou `"Acordes"`. Caso não exista, ele faz um fallback automático para a primeira faixa MIDI contendo eventos de texto.
2. **Sincronização Temporal:** As posições das notas e eventos MIDI são convertidos de ticks para segundos usando o BPM do projeto ou o marcador `IGNTEMPO`.
3. **Grade de Compassos (Chord Grid) com Síncopas e Antecipações:**
   - Agrupa os acordes por região e formata os compassos na métrica do projeto (ex: 4/4).
   - Usa o caractere de bloco espesso `┃` (`\u2503`) como divisor vertical para alinhamento legível em telas móveis.
   - **Modificadores Rítmicos**:
     - `←Acorde` (Antecipação): Indica que o acorde é tocado no contratempo (uma colcheia antes do tempo nominal).
     - `→Acorde` (Atraso): Indica que o acorde é empurrado para o contratempo posterior (uma colcheia após o tempo nominal).
   - **Slash de Tempo Forte (`/`)**: Utilizado em compassos não uniformes para indicar a marcação das batidas fortes.
   - **Modo Compacto Inteligente**:
     - Compassos uniformes (onde um único acorde dura o compasso inteiro) são simplificados para apenas `┃ Grau ┃` (sem `/` desnecessários).
     - `%` indica repetição do compasso inteiro e `-` representa silêncio ou compasso vazio.
