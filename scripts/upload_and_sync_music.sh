#!/bin/bash

# Script para selecionar uma pasta local de música, enviar ao OneDrive e publicar no Telegram.
# Pode ser acionado diretamente pelo aplicativo Atalhos (Shortcuts), Automator ou terminal.

# Vai para o diretório raiz do projeto
cd "/Users/marques/Documents/Pessoal/organization-praise-ministry-automatization" || exit 1

# Ativa o ambiente virtual
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Ambiente virtual não encontrado em venv/bin/activate" >&2
    exit 1
fi

echo "Abrindo seletor de pasta..."

# 1. Abre o seletor nativo posicionado no diretório de projetos da igreja
PASTA_ESCOLHIDA=$(osascript -l JavaScript scripts/seletor_pasta_upload.js)

# 2. Se cancelou, encerra silenciosamente
if [ -z "$PASTA_ESCOLHIDA" ]; then
    echo "Operação cancelada pelo usuário."
    exit 0
fi

NOME_PASTA=$(basename "$PASTA_ESCOLHIDA")
echo "Pasta selecionada: $NOME_PASTA"
echo "Caminho: $PASTA_ESCOLHIDA"

osascript -e "display notification \"Iniciando upload para o OneDrive...\" with title \"Upload em Andamento\" subtitle \"$NOME_PASTA\""

# 3. Executa o upload para o OneDrive (cria a pasta remota e sobe recursivamente)
UPLOAD_LOG=$(mktemp /tmp/upload_music.XXXXXX.log)
trap 'rm -f "$UPLOAD_LOG"' EXIT

REMOTE_FOLDER_ID=$(venv/bin/python -m runners.upload_music --local-path "$PASTA_ESCOLHIDA" 2> "$UPLOAD_LOG" | tr -d '\r\n')
UPLOAD_STATUS=$?

if [ $UPLOAD_STATUS -ne 0 ] || [ -z "$REMOTE_FOLDER_ID" ]; then
    echo "Falha no upload para o OneDrive." >&2
    ULTIMA_LINHA=$(tail -n 2 "$UPLOAD_LOG" | tr '\n' ' ')
    osascript -e "display alert \"Erro no Upload\" message \"Falha ao enviar a pasta '$NOME_PASTA' para o OneDrive.\n\nDetalhes: $ULTIMA_LINHA\" as critical"
    exit 1
fi

echo "Upload para o OneDrive concluído com sucesso! (ID: $REMOTE_FOLDER_ID)"
echo "Iniciando sincronização e publicação no Telegram..."

osascript -e "display notification \"Enviando áudios e arranjos para o Telegram...\" with title \"Sincronizando Música\" subtitle \"$NOME_PASTA\""

# 4. Sincroniza e envia a nova música para o Telegram com --force
venv/bin/python -m runners.sync_music --folder-id "$REMOTE_FOLDER_ID" --force

STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "Música '$NOME_PASTA' enviada ao OneDrive e publicada no Telegram com sucesso!"
    osascript -e "display notification \"Música enviada ao OneDrive e publicada com sucesso no Telegram!\" with title \"Tudo Concluído!\" subtitle \"$NOME_PASTA\" sound name \"Glass\""
else
    echo "Erro durante o envio para o Telegram." >&2
    osascript -e "display alert \"Aviso\" message \"A pasta foi enviada ao OneDrive, mas ocorreu uma falha ao sincronizar com o Telegram.\" as critical"
    exit $STATUS
fi
