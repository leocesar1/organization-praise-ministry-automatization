#!/bin/bash

# Script para baixar uma pasta de música completa do OneDrive para a pasta Downloads do Mac.
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

echo "Buscando músicas no OneDrive..."
TMP_JSON=$(mktemp /tmp/musicas_download.XXXXXX.json)
trap 'rm -f "$TMP_JSON"' EXIT

# 1. Busca a lista de músicas do OneDrive dinamicamente
venv/bin/python -m runners.list_musics > "$TMP_JSON"

if [ ! -s "$TMP_JSON" ]; then
    osascript -e 'display alert "Erro no OneDrive" message "Não foi possível carregar a lista de músicas do OneDrive." as critical'
    exit 1
fi

# 2. Executa o formulário nativo JXA
ESCOLHA=$(osascript -l JavaScript scripts/formulario_download_musica.js "$TMP_JSON")

# 3. Se o usuário cancelou ou fechou, encerra
if [ -z "$ESCOLHA" ]; then
    echo "Operação cancelada pelo usuário."
    exit 0
fi

# 4. Extrai o ID e o nome da música selecionada
FOLDER_ID=$(echo "$ESCOLHA" | venv/bin/python -c "import sys, json; print(json.load(sys.stdin).get('folder_id', ''))")
MUSIC_NAME=$(echo "$ESCOLHA" | venv/bin/python -c "import sys, json; print(json.load(sys.stdin).get('name', ''))")

if [ -z "$FOLDER_ID" ]; then
    echo "ID da música inválido." >&2
    exit 1
fi

echo "Iniciando download de '$MUSIC_NAME'..."

# 5. Executa o download da pasta inteira para ~/Downloads
DEST_PATH=$(venv/bin/python -m runners.download_music --folder-id "$FOLDER_ID" --dest-dir "$HOME/Downloads" | tail -n 1)

STATUS=$?
if [ $STATUS -eq 0 ] && [ -n "$DEST_PATH" ] && [ -d "$DEST_PATH" ]; then
    echo "Download concluído em: $DEST_PATH"
    osascript -e "display notification \"Pasta completa baixada em Downloads.\" with title \"Download Concluído!\" subtitle \"$MUSIC_NAME\" sound name \"Glass\""
    # Abre a pasta baixada diretamente no Finder
    open "$DEST_PATH"
else
    echo "Erro ao baixar a música." >&2
    osascript -e "display alert \"Erro no Download\" message \"Ocorreu um erro ao baixar a música '$MUSIC_NAME'. Verifique o terminal para detalhes.\" as critical"
    exit $STATUS
fi
