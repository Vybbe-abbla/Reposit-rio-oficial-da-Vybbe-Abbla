# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv

# Configurações gerais do app
st.set_page_config(page_title="Análise de Sentimentos - VADER", layout="wide")

st.title("📊 Análise de Sentimentos — Versão leve (VADER)")
st.markdown(
    "Este app analisa comentários e classifica como **Positivo**, **Neutro** ou **Negativo**. "
    "Compatível com Python 3.13 e arquivos CSV com ponto e vírgula (;)."
)

# Upload do arquivo
uploaded_file = st.sidebar.file_uploader("📂 Carregue a planilha CSV com os comentários", type=["csv"])

if uploaded_file is None:
    st.warning("Envie um arquivo CSV contendo a coluna `comente` ou similar.")
    st.stop()

# --- LEITURA AUTOMÁTICA DO CSV ---
def read_csv_auto(file):
    # Detectar o separador (vírgula ou ponto e vírgula)
    sample = file.read(2048).decode("utf-8", errors="ignore")
    file.seek(0)
    sep = ";" if sample.count(";") > sample.count(",") else ","

    # Tentar ler com UTF-8, se falhar tenta Latin-1
    try:
        df = pd.read_csv(file, sep=sep, quoting=csv.QUOTE_MINIMAL, encoding="utf-8")
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=sep, quoting=csv.QUOTE_MINIMAL, encoding="latin-1")
    return df

try:
    df = read_csv_auto(uploaded_file)
except Exception as e:
    st.error(f"❌ Erro ao ler o CSV: {e}")
    st.stop()

st.success(f"Arquivo lido com sucesso! {df.shape[0]} linhas e {df.shape[1]} colunas detectadas.")
st.write("### Visualização inicial dos dados:")
st.dataframe(df.head(10))

# --- DETECTAR COLUNA DE COMENTÁRIOS ---
colunas_lower = [c.lower() for c in df.columns]
possiveis = [df.columns[i] for i, c in enumerate(colunas_lower) if "coment" in c or "mensagem" in c or "texto" in c]

if possiveis:
    col_coment = possiveis[0]
    st.info(f"Coluna detectada automaticamente: **{col_coment}**")
else:
    col_coment = st.selectbox("Selecione a coluna com os comentários", df.columns)

comentarios = df[col_coment].dropna().astype(str)

# --- ANÁLISE DE SENTIMENTO ---
st.info("🔍 Analisando sentimentos (isso leva alguns segundos)...")

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positivo"
    elif score <= -0.05:
        return "Negativo"
    else:
        return "Neutro"

df["Sentimento"] = comentarios.apply(get_sentiment)

# --- RESUMO E GRÁFICO ---
resumo = (
    df["Sentimento"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
    .reindex(["Negativo", "Neutro", "Positivo"])
    .fillna(0)
    .reset_index()
)
resumo.columns = ["Sentimento", "Percentual (%)"]

st.subheader("📈 Distribuição dos Sentimentos")
fig = px.bar(
    resumo,
    x="Sentimento",
    y="Percentual (%)",
    text="Percentual (%)",
    title="Distribuição de Sentimentos (%)",
    range_y=[0, 100],
)
fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True)

# --- EXEMPLOS DE CADA CATEGORIA ---
st.subheader("💬 Exemplos de Comentários por Categoria")
for cat in ["Negativo", "Neutro", "Positivo"]:
    exemplos = df[df["Sentimento"] == cat][col_coment].head(5)
    if len(exemplos) > 0:
        st.markdown(f"**{cat}** ({len(exemplos)} exemplos):")
        for e in exemplos:
            st.write(f"- {e}")
    else:
        st.write(f"Sem exemplos detectados para **{cat}**.")

# --- EXPORTAÇÃO OPCIONAL ---
st.download_button(
    "⬇️ Baixar resultados em CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="analise_sentimentos.csv",
    mime="text/csv",
)

st.success("✅ Análise concluída com sucesso!")
