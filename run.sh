#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python src/baixar_dados.py
python src/gerar_html_estatico.py
echo "Para o app interativo: streamlit run src/app.py"
