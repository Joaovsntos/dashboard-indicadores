#!/usr/bin/env python3
"""Baixa séries do BCB SGS e salva CSV local para o dashboard."""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SERIES = {
    433: "IPCA (% a.m.)",
    13522: "IPCA acumulado 12 meses (%)",
    432: "Selic Meta (% a.a.)",
    1: "USD/BRL PTAX (R$)",
    189: "IGP-M (% a.m.)",
}

INICIOS = {
    433: "01/01/2019",
    13522: "01/01/2019",
    432: "01/01/2019",
    1: "01/01/2020",
    189: "01/01/2019",
}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    DATA.mkdir(parents=True, exist_ok=True)
    fim = datetime.now().strftime("%d/%m/%Y")
    frames = []
    for codigo, nome in SERIES.items():
        url = (
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
            f"?formato=json&dataInicial={INICIOS[codigo]}&dataFinal={fim}"
        )
        logging.info("Baixando %s...", nome)
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["data"] = pd.to_datetime(df["data"], dayfirst=True)
        df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce")
        df["serie"] = nome
        df["codigo_sgs"] = codigo
        frames.append(df[["data", "valor", "serie", "codigo_sgs"]])
        logging.info("  %d pontos", len(df))
    out = pd.concat(frames, ignore_index=True).dropna(subset=["valor"])
    path = DATA / "indicadores_bcb.csv"
    out.to_csv(path, index=False, encoding="utf-8")
    meta = DATA / "FONTE.txt"
    meta.write_text(
        "Fonte: Banco Central do Brasil — Sistema Gerenciador de Séries Temporais (SGS)\n"
        "API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json\n"
        "Séries: IPCA (433), IPCA 12m (13522), Selic Meta (432), USD PTAX venda (1), IGP-M (189)\n"
        f"Extraído em: {datetime.now().isoformat(timespec='seconds')}\n",
        encoding="utf-8",
    )
    logging.info("Salvo em %s (%d linhas)", path, len(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
