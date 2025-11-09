import re
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import csv
import os
from groq import Groq  # pip install groq

# ============ CONFIGURAÇÕES GERAIS ============
st.set_page_config(page_title="Análise de Sentimentos - Agência", layout="wide")

st.title("🎵 Análise de Sentimentos — Evento Musical")
st.markdown(
    """
    Este painel realiza automaticamente uma **análise de sentimentos** dos comentários sobre o evento,
    classificando-os como **Negativos**, **Neutros** ou **Positivos** com base na API da **Groq**.
    """
)
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# ================== UPLOAD DO CSV ==================
uploaded_file = st.sidebar.file_uploader("📂 Carregue o CSV com os comentários", type=["csv"])
if uploaded_file is None:
    st.warning("Envie um arquivo CSV com a coluna de comentários (ex: 'comente').")
    st.stop()

# ================== LEITURA AUTOMÁTICA ==================
def read_csv_auto(file):
    sample = file.read(2048).decode("utf-8", errors="ignore")
    file.seek(0)
    sep = ";" if sample.count(";") > sample.count(",") else ","
    try:
        df = pd.read_csv(file, sep=sep, quoting=csv.QUOTE_MINIMAL, encoding="utf-8")
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=sep, quoting=csv.QUOTE_MINIMAL, encoding="latin-1")
    return df

df = read_csv_auto(uploaded_file)

# ================== DETECTAR COLUNA DE COMENTÁRIOS ==================
colunas_lower = [c.lower() for c in df.columns]
possiveis = [df.columns[i] for i, c in enumerate(colunas_lower) if "comente" in c or "mensagem" in c or "texto" in c]
col_coment = possiveis[0] if possiveis else df.columns[0]
comentarios = df[col_coment].dropna().astype(str).tolist()

# ================== FUNÇÃO DE ANÁLISE EM LOTE ==================
_LABEL_RE = re.compile(r"\b(negativo|neutro|positivo)\b", flags=re.IGNORECASE)

def analisar_lote(lote, max_retries=1, sleep_on_retry=0.5):
    """
    Recebe até N comentários e retorna lista de classificações ('Positivo','Neutro','Negativo').
    """
    texto = "\n".join([f"{i+1}. {c}" for i, c in enumerate(lote)])
    prompt = f"""
Você é um analista de redes sociais experiente, especializado em avaliar o sentimento de comentários sobre eventos musicais.

Classifique cada comentário abaixo como **Negativo**, **Neutro** ou **Positivo**, conforme o tom emocional predominante.

**Critérios de interpretação:**
- **Negativo:** expressa raiva, frustração, ironia, decepção, deboche, reclamação, crítica, ou qualquer emoção negativa — mesmo que de forma sutil ou sarcástica.
- **Neutro:** é apenas informativo, contém perguntas, risadas (“kkk”, “haha”), emojis sem emoção clara, ou não demonstra sentimento forte.
- **Positivo:** expressa apoio, alegria, empolgação, elogio, satisfação ou humor leve e simpático.

**Instruções importantes:**
- Analise o tom e o contexto, não apenas palavras isoladas.
- Se o comentário tiver elementos negativos e positivos, escolha o que for **mais evidente emocionalmente**.
- Evite classificar como “Neutro” por indecisão: use apenas quando realmente **não houver emoção**.
- Responda listando **somente as palavras “Negativo”, “Neutro” ou “Positivo”**, uma por comentário, na ordem apresentada.

Exemplos:
1. "O show foi horrível, uma decepção!" → Negativo
2. "Nem ligo, acontece." → Neutro
3. "Foi incrível, mesmo sem o artista principal!" → Positivo


Comentários:
{texto}

"""
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Você é um analista de sentimentos em português."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=512
            )
            raw = resp.choices[0].message.content.strip()
            linhas = [l.strip() for l in raw.splitlines() if l.strip()]
            parsed = []
            for linha in linhas:
                m = _LABEL_RE.search(linha)
                if m:
                    parsed.append(m.group(1).capitalize())
            if len(parsed) == len(lote):
                return parsed
            if len(parsed) > len(lote):
                return parsed[:len(lote)]

            # Fallback individual
            fallback = []
            for c in lote:
                prompt_single = f"Classifique este comentário como Negativo, Neutro ou Positivo: {c}"
                r = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt_single}],
                    temperature=0,
                    max_tokens=20
                )
                raw_single = r.choices[0].message.content.strip()
                m = _LABEL_RE.search(raw_single)
                fallback.append(m.group(1).capitalize() if m else "Neutro")
            return fallback
        except Exception as e:
            if attempt < max_retries:
                time.sleep(sleep_on_retry)
                continue
            return ["Neutro"] * len(lote)

# ================== EXECUÇÃO AUTOMÁTICA ==================
st.info("🔍 Iniciando análise dos comentários...")
resultados = []
lote_tamanho = 10
progress = st.progress(0)

for i in range(0, len(comentarios), lote_tamanho):
    lote = comentarios[i:i+lote_tamanho]
    classificacoes = analisar_lote(lote)
    if len(classificacoes) != len(lote):
        if len(classificacoes) < len(lote):
            classificacoes.extend(["Neutro"] * (len(lote) - len(classificacoes)))
        else:
            classificacoes = classificacoes[:len(lote)]
    resultados.extend(classificacoes)
    progress.progress(min((i + lote_tamanho) / len(comentarios), 1.0))

if len(resultados) < len(df):
    resultados.extend(["Neutro"] * (len(df) - len(resultados)))

df["Sentimento"] = resultados

# ================== RESULTADOS ==================
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

# ---------- CARD DE TOTAL ----------
total_comentarios = len(df)
st.markdown(f"""
<div style='background-color:#F0F2F6; padding:20px; border-radius:10px; text-align:center'>
    <h3>💬 Total de comentários analisados: <b>{total_comentarios}</b></h3>
</div>
""", unsafe_allow_html=True)

# ---------- GRÁFICO ----------
st.subheader("📊 Distribuição dos Sentimentos")
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

# ---------- COMENTÁRIO AUTOMÁTICO DA IA ----------
st.subheader("🧠 Análise da IA sobre os comentários")

prompt_resumo = f"""
Com base nas porcentagens:
{resumo.to_string(index=False)}

E levando em conta o contexto de um evento musical onde um artista faltou,
faça um resumo objetivo e empático sobre o que isso demonstra sobre o público.
Use tom profissional e comunicativo.
"""

resposta_resumo = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt_resumo}],
    temperature=0.7,
    max_tokens=200
)
analise_texto = resposta_resumo.choices[0].message.content.strip()
st.write(analise_texto)

# ---------- INTERAÇÃO COM O USUÁRIO ----------
st.subheader("💬 Converse com a IA sobre o assunto")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

pergunta = st.text_input("Digite sua pergunta ou comentário:")
if pergunta:
    st.session_state.chat_history.append({"role": "user", "content": pergunta})
    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Você é uma assistente empática e profissional de marketing musical."},
            *st.session_state.chat_history
        ],
        temperature=0.7,
        max_tokens=300
    )
    resposta_texto = resposta.choices[0].message.content.strip()
    st.session_state.chat_history.append({"role": "assistant", "content": resposta_texto})

# Mostrar o histórico de conversa
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💻 **Você:** {msg['content']}")
    else:
        st.markdown(f"🤖 **IA:** {msg['content']}")
