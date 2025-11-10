import re
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import csv
import os
from groq import Groq
from textblob import TextBlob
from PIL import Image

# ============ CONFIGURAÇÕES GERAIS ============
st.set_page_config(page_title="Habbla", layout="wide")

st.title("🎵 Reports de Crise - Análise de Sentimentos")

st.markdown(
    """
    Este painel realiza automaticamente uma **análise de sentimentos** dos comentários sobre o evento,
    classificando-os como **Negativos**, **Neutros** ou **Positivos** com base na API da **Groq**.
    """
)

# ============ CHAVE DA API ============
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("❌ Não foi possível carregar a chave da API Groq. Verifique seu arquivo `secrets.toml`.")
    st.stop()

# ================== UPLOAD DO CSV ==================
st.sidebar.image("logo_habbla_cor_positivo.png", width=160)

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

# ================== ANÁLISE DE SENTIMENTOS ==================
_LABEL_RE = re.compile(r"\b(negativo|neutro|positivo)\b", flags=re.IGNORECASE)

def sentimento_preliminar(texto):
    analise = TextBlob(texto)
    if analise.sentiment.polarity > 0.1:
        return "Positivo"
    elif analise.sentiment.polarity < -0.1:
        return "Negativo"
    return "Neutro"


def analisar_lote(lote, max_retries=3, sleep_on_retry=5):
    preliminares = [sentimento_preliminar(c) for c in lote]
    texto = "\n".join([
        f"{i+1}. Comentário: {c}\nAnálise preliminar: {preliminares[i]}"
        for i, c in enumerate(lote)
    ])

    prompt = f"""
Você é um analista de sentimentos especialista em redes sociais e eventos musicais.
Sua tarefa é identificar o **tom emocional predominante** de cada comentário.

Classifique cada comentário como:
- **Positivo:** demonstra alegria, empolgação, amor, elogio, satisfação ou apoio.
- **Negativo:** demonstra raiva, frustração, decepção, crítica, ironia, deboche ou sarcasmo.
- **Neutro:** é informativo, contém apenas emojis, risadas (“kkk”, “haha”), ou não demonstra emoção clara.

⚠️ Instruções importantes:
- Analise o **tom e o contexto emocional completo**, não apenas palavras isoladas.
- Considere a “análise preliminar” como um ponto de partida, mas **corrija se estiver errada**.
- Se o comentário tiver indícios de emoção, **nunca classifique como Neutro** — use Neutro apenas se não houver emoção.
- Responda somente com uma palavra por linha: **Negativo**, **Neutro** ou **Positivo**.
- Respeite a ordem dos comentários.

Comentários:

{texto}
"""

    for attempt in range(max_retries):
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
            if len(parsed) >= len(lote):
                return parsed[:len(lote)]
            else:
                raise ValueError("Resposta incompleta ou inconsistente.")
        except Exception as e:
            erro = str(e)
            if "rate_limit_exceeded" in erro:
                wait_time = 90
                st.warning(f"⚠️ Limite da API atingido. Aguardando {wait_time}s e tentando novamente...")
                time.sleep(wait_time)
                continue
            elif attempt < max_retries - 1:
                st.info("Tentando novamente após erro temporário...")
                time.sleep(sleep_on_retry)
                continue
            else:
                st.error(f"❌ Erro persistente na API: {erro}")
                # Fallback simples com modelo menor
                try:
                    alt = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0,
                        max_tokens=512
                    )
                    raw_alt = alt.choices[0].message.content.strip()
                    parsed_alt = []
                    for linha in raw_alt.splitlines():
                        m = _LABEL_RE.search(linha)
                        if m:
                            parsed_alt.append(m.group(1).capitalize())
                    return parsed_alt[:len(lote)]
                except:
                    return ["Neutro"] * len(lote)
    return ["Neutro"] * len(lote)

# ================== EXECUÇÃO AUTOMÁTICA ==================
st.info("🔍 Iniciando análise dos comentários...")
resultados = []
lote_tamanho = 10
progress = st.progress(0)

for i in range(0, len(comentarios), lote_tamanho):
    lote = comentarios[i:i+lote_tamanho]
    classificacoes = analisar_lote(lote)
    resultados.extend(classificacoes)
    progress.progress(min((i + lote_tamanho) / len(comentarios), 1.0))

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

# Campo para o usuário informar o contexto da crise/evento
contexto_usuario = st.text_area(
    "📝 Descreva brevemente o contexto do evento ou situação:",
    placeholder="Exemplo: O artista principal cancelou o show de última hora, gerando reações mistas nas redes sociais."
)

# Só gera o resumo se o usuário preencher o contexto
if st.button("Gerar análise da IA"):
    if not contexto_usuario.strip():
        st.warning("Por favor, insira o contexto antes de gerar a análise.")
    else:
        try:
            prompt_resumo = f"""
Com base nas porcentagens:
{resumo.to_string(index=False)}

Contexto informado:
{contexto_usuario}

Gere um resumo empático e objetivo sobre o sentimento geral do público.
Mostre o que os comentários revelam sobre a percepção do evento.
Use um tom profissional e comunicativo, adequado para um **report de crise ou análise de reputação**.
"""

            resposta_resumo = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt_resumo}],
                temperature=0.7,
                max_tokens=250
            )
            analise_texto = resposta_resumo.choices[0].message.content.strip()
            st.success("✅ Análise gerada com sucesso!")
            st.write(analise_texto)

        except Exception as e:
            if "rate_limit_exceeded" in str(e):
                st.warning("⚠️ Limite diário da API atingido. Tente novamente mais tarde.")
            else:
                st.error(f"❌ Erro ao gerar análise da IA: {e}")

# ---------- INTERAÇÃO COM O USUÁRIO ----------
st.subheader("💬 Converse com a IA sobre o assunto")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

pergunta = st.text_input("Digite sua pergunta ou comentário:")
if pergunta:
    try:
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
    except Exception as e:
        if "rate_limit_exceeded" in str(e):
            st.warning("⚠️ Limite diário da API atingido. Tente novamente amanhã.")
        else:
            st.error(f"❌ Erro ao responder: {e}")

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💻 **Você:** {msg['content']}")
    else:
        st.markdown(f"🤖 **IA:** {msg['content']}")
