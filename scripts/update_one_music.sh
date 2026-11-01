#!/bin/bash

# Script para atualizar uma música específica selecionada através de formulário nativo do macOS.
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
TMP_JSON=$(mktemp /tmp/musicas_onedrive.XXXXXX.json)
trap 'rm -f "$TMP_JSON"' EXIT

# 1. Busca a lista de músicas do OneDrive dinamicamente salvando em arquivo temporário
venv/bin/python -m runners.list_musics > "$TMP_JSON"

if [ ! -s "$TMP_JSON" ]; then
    osascript -e 'display alert "Erro no OneDrive" message "Não foi possível carregar a lista de músicas do OneDrive." as critical'
    exit 1
fi

# 2. Executa o formulário nativo JXA passando o arquivo
ESCOLHA=$(osascript -l JavaScript scripts/formulario_musica.js "$TMP_JSON")

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

echo "Iniciando atualização de '$MUSIC_NAME' (ID: $FOLDER_ID)..."

# 5. Executa a sincronização forçada (áudios + arranjo .rpp)
venv/bin/python -m runners.sync_music --folder-id "$FOLDER_ID" --force

STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "Música '$MUSIC_NAME' atualizada com sucesso!"
    osascript -e "display notification \"Áudios e arranjos sincronizados com sucesso no Telegram.\" with title \"Música Atualizada!\" subtitle \"$MUSIC_NAME\" sound name \"Glass\""
else
    echo "Erro ao atualizar a música." >&2
    osascript -e "display alert \"Erro na Atualização\" message \"Ocorreu um erro ao atualizar a música '$MUSIC_NAME'. Verifique o terminal para detalhes.\" as critical"
    exit $STATUS
fi
