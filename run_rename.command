#!/bin/bash

# Este script pode ser executado via aplicativo Atalhos (Shortcuts) do Mac, 
# Automator, ou apenas com um duplo-clique no Finder.

# Vai para o diretório do projeto
cd "/Users/marques/Documents/Pessoal/organization-praise-ministry-automatization" || exit

# Ativa o ambiente virtual
source venv/bin/activate

# Executa o script de renomeação do OneDrive
echo "Iniciando a renomeação do OneDrive..."
python -m runners.rename_onedrive --execute

echo ""
echo "Renomeação concluída!"
