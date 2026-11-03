#!/usr/bin/env python3
"""Dashboard interativo de indicadores macroeconômicos (Streamlit)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "indicadores_bcb.csv"

st.set_page_config(
    page_title="Indicadores Macro — Brasil",
    page_icon="📊",
    layout="wide",
)

st.title("Indicadores Macroeconômicos — Brasil")
st.caption(
    "Fonte: Banco Central do Brasil (SGS). Dados públicos via API oficial. "
    "Projeto de portfólio — Python + Streamlit + Plotly."
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA.exists():
        st.error("Arquivo de dados não encontrado. Rode: python src/baixar_dados.py")
        st.stop()
    df = pd.read_csv(DATA, parse_dates=["data"])
    return df


df = load_data()
series = sorted(df["serie"].unique())
anos = sorted(df["data"].dt.year.unique())

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    escolhidas = st.multiselect("Séries", series, default=series[:3])
with c2:
    ano_min, ano_max = st.select_slider(
        "Período (ano)",
        options=anos,
        value=(anos[0], anos[-1]),
    )
with c3:
    freq = st.selectbox("Agregação do câmbio", ["diária", "mensal (média)"], index=1)

filtro = df[
    (df["serie"].isin(escolhidas))
    & (df["data"].dt.year >= ano_min)
    & (df["data"].dt.year <= ano_max)
].copy()

# KPIs
kpis = []
for s in escolhidas:
    sub = filtro[filtro["serie"] == s].sort_values("data")
    if sub.empty:
        continue
    ultimo = sub.iloc[-1]
    prev = sub.iloc[-2]["valor"] if len(sub) > 1 else None
    delta = None if prev is None else ultimo["valor"] - prev
    kpis.append((s, ultimo["valor"], delta, ultimo["data"]))

cols = st.columns(max(len(kpis), 1))
for i, (nome, valor, delta, dt) in enumerate(kpis):
    with cols[i]:
        st.metric(
            label=f"{nome}",
            value=f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            delta=None
            if delta is None
            else f"{delta:+,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            help=f"Última observação: {dt.date()}",
        )

# Gráfico principal
plot_df = filtro.copy()
if freq.startswith("mensal"):
    mask_fx = plot_df["serie"].str.contains("USD", case=False)
    diario = plot_df.loc[mask_fx].copy()
    if not diario.empty:
        diario["mes"] = diario["data"].values.astype("datetime64[M]")
        agg = diario.groupby(["mes", "serie", "codigo_sgs"], as_index=False)["valor"].mean()
        agg = agg.rename(columns={"mes": "data"})
        plot_df = pd.concat([plot_df.loc[~mask_fx], agg], ignore_index=True)

fig = px.line(
    plot_df.sort_values("data"),
    x="data",
    y="valor",
    color="serie",
    markers=False,
    title="Evolução das séries selecionadas",
)
fig.update_layout(legend_title_text="Série", hovermode="x unified", height=480)
st.plotly_chart(fig, use_container_width=True)

# Comparativo IPCA 12m x Selic
st.subheader("IPCA 12 meses × Selic Meta")
ipca12 = df[df["codigo_sgs"] == 13522].sort_values("data")
selic = df[df["codigo_sgs"] == 432].sort_values("data")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=ipca12["data"], y=ipca12["valor"], name="IPCA 12m (%)", line=dict(width=2)))
fig2.add_trace(go.Scatter(x=selic["data"], y=selic["valor"], name="Selic Meta (% a.a.)", line=dict(width=2)))
fig2.update_layout(height=420, hovermode="x unified", legend_title_text="")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Tabela (amostra)")
st.dataframe(
    filtro.sort_values(["serie", "data"], ascending=[True, False]).head(200),
    use_container_width=True,
)

st.markdown(
    """
---
**Como reproduzir em Power BI:** veja o README do repositório (guia passo a passo).  
Não é possível gerar arquivo `.pbix` neste ambiente Linux; o modelo de dados e as medidas DAX equivalentes estão documentados.
"""
)
