#!/usr/bin/env python3
"""Gera um HTML Plotly estático (útil para capa/portfólio sem servidor Streamlit)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "indicadores_bcb.csv"
OUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["data"])

# Painel
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "IPCA mensal (%)",
        "IPCA acumulado 12 meses (%)",
        "Selic Meta (% a.a.)",
        "USD/BRL PTAX (média mensal)",
    ),
    vertical_spacing=0.12,
    horizontal_spacing=0.08,
)

def add_line(codigo, row, col, color):
    sub = df[df["codigo_sgs"] == codigo].sort_values("data")
    if codigo == 1:
        sub = (
            sub.assign(mes=sub["data"].values.astype("datetime64[M]"))
            .groupby("mes", as_index=False)["valor"]
            .mean()
            .rename(columns={"mes": "data"})
        )
    fig.add_trace(
        go.Scatter(x=sub["data"], y=sub["valor"], mode="lines", line=dict(color=color, width=2), showlegend=False),
        row=row,
        col=col,
    )

add_line(433, 1, 1, "#1F4E79")
add_line(13522, 1, 2, "#C45911")
add_line(432, 2, 1, "#548235")
add_line(1, 2, 2, "#833C0C")

fig.update_layout(
    title=dict(
        text="Indicadores Macroeconômicos do Brasil — Banco Central (SGS)",
        x=0.5,
        font=dict(size=20, color="#1F4E79"),
    ),
    height=800,
    width=1400,
    template="plotly_white",
    margin=dict(t=80, l=50, r=30, b=40),
)
path = OUT / "dashboard_indicadores.html"
fig.write_html(path, include_plotlyjs="cdn", full_html=True)
print("HTML:", path)

# também exporta PNG via kaleido se disponível
try:
    png = OUT / "dashboard_preview.png"
    fig.write_image(str(png), scale=2)
    print("PNG:", png)
except Exception as exc:
    print("PNG não gerado:", exc)
