import streamlit as st
import pandas as pd
import plotly.express as px
import csv
import re
from openai import OpenAI
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob
from PIL import Image

# ======Configurações inciais ============

st.set_page_config(page_title="Habbla", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #E11D48;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ============ Configuração perplexity ============
try:
    pplx_api_key = st.secrets["PERPLEXITY_API_KEY"]
    client = OpenAI(api_key=pplx_api_key, base_url="https://api.perplexity.ai")
    MODELO_RAG = "sonar"          # Para chat e análise de dados locais
    MODELO_RESEARCH = "sonar-pro" # Para análise com busca na internet
except Exception as e:
    st.error("❌ Erro ao carregar API Key da Perplexity.")
    st.stop()

# ============ FUNÇÕES DE SUPORTE ============

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

def sentimento_preliminar(texto):
    analise = TextBlob(texto)
    if analise.sentiment.polarity > 0.1: return "Positivo"
    elif analise.sentiment.polarity < -0.1: return "Negativo"
    return "Neutro"

def analisar_lote_sentimento(lote):
    _LABEL_RE = re.compile(r"\b(negativo|neutro|positivo)\b", flags=re.IGNORECASE)
    preliminares = [sentimento_preliminar(c) for c in lote]
    texto_lote = "\n".join([f"{i+1}. Comentário: {c} | Preliminar: {preliminares[i]}" for i, c in enumerate(lote)])
    prompt = f"Classifique o sentimento (Positivo, Negativo ou Neutro) destes comentários:\n{texto_lote}"
    try:
        response = client.chat.completions.create(
            model=MODELO_RAG,
            messages=[{"role": "system", "content": "Você é um classificador local técnico."},
                      {"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        linhas = [l.strip() for l in raw.splitlines() if l.strip()]
        parsed = []
        for linha in linhas:
            m = _LABEL_RE.search(linha)
            if m: parsed.append(m.group(1).capitalize())
        return parsed[:len(lote)] if len(parsed) >= len(lote) else ["Neutro"] * len(lote)
    except:
        return ["Neutro"] * len(lote)

#== Interface principal
rodape_image = Image.open('habbla_rodape.jpg')
st.image(rodape_image, width=110)

st.write("---")

st.title("🎵 Habbla - Painel Monitoramento de Crise")

st.sidebar.header("Painel de Controle")
uploaded_file = st.sidebar.file_uploader("📂 Carregue o arquivo CSV", type=["csv"])

if uploaded_file:
    df = read_csv_auto(uploaded_file)
    
    colunas_lower = [c.lower() for c in df.columns]
    possiveis = [df.columns[i] for i, c in enumerate(colunas_lower) if any(x in c for x in ["comente", "mensagem", "texto"])]
    col_coment = possiveis[0] if possiveis else df.columns[0]
    
    # Card de Métrica
    
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #10B981; /* Cor Verde */
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    total_coments = len(df)
    # Formata com vírgula e depois troca para ponto
    total_formatado = f"{total_coments:,}".replace(",", ".")

    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #64748b; font-size: 14px; font-weight: bold;">TOTAL DE COMENTÁRIOS ANALISADOS</span>
        <h2 style="color: #1E3A8A;">{total_formatado}</h2>
    </div>
    """, unsafe_allow_html=True)

    # 2. Contexto e Diagnóstico (Com Busca na Internet e Persistência)
    st.subheader("📝 Contexto do Evento")
    contexto_usuario = st.text_area("Explique o que aconteceu e cite o artista da agêcia:", 
                                     placeholder="Ex: Incidente com Zé Vaqueiro e sua equipe...",
                                     key="input_contexto")

    if st.button("🚀 Gerar Diagnóstico de Crise"):
        if not contexto_usuario:
            st.warning("Por favor, descreva o contexto para análise.")
        else:
            with st.spinner("Analisando narrativas locais e contextualizando com o histórico do artista na internet..."):
                amostra = "\n".join(df[col_coment].astype(str).head(150).tolist())
                
                # Prompt atualizado para permitir busca e análise de proporção
                prompt_diag = f"""
                Você é um estrategista de reputação sênior. 
                
                DADOS LOCAIS (Comentários):
                {amostra}
                
                CONTEXTO: {contexto_usuario}
                
                TAREFA:
                1. Gere um diagnóstico de narrativa (Tendência, Polarização, Tom e Riscos).
                2. PESQUISE NA INTERNET o tamanho atual e o histórico do artista citado. 
                3. Analise qual o impacto real desta crise específica dentro do "universo" (carreira/base de fãs) do artista. Ela é uma crise periférica, média ou estrutural?

                não invente noticias ou fatos da internet, baseie-se apenas em informações reais e verificáveis.
                
                (Não sugira planos de ação). Responda com autoridade.
                """
                
                diag_resp = client.chat.completions.create(
                    model=MODELO_RESEARCH, # sonar-pro para busca online
                    messages=[{"role": "user", "content": prompt_diag}]
                )
                st.session_state.texto_diagnostico = diag_resp.choices[0].message.content

    # Manter o diagnóstico visível
    if "texto_diagnostico" in st.session_state:
        st.info("### Diagnóstico e Contextualização de Crise")
        st.markdown(st.session_state.texto_diagnostico)

    st.divider()

    # 3. Sentimentos (Cache no session_state)
    if 'sentimento_processado' not in st.session_state:
        with st.spinner("Analisando sentimentos..."):
            comentarios_lista = df[col_coment].dropna().astype(str).tolist()
            resultados = []
            for i in range(0, len(comentarios_lista), 10):
                resultados.extend(analisar_lote_sentimento(comentarios_lista[i:i+10]))
            df["Sentimento"] = resultados
            st.session_state.sentimento_processado = df["Sentimento"]
    else:
        df["Sentimento"] = st.session_state.sentimento_processado

    st.subheader("📊 Distribuição de Sentimentos")
    resumo = df["Sentimento"].value_counts(normalize=True).mul(100).round(2).reset_index()
    resumo.columns = ["Sentimento", "Percentual"] 
    fig_sent = px.bar(resumo, x="Sentimento", y="Percentual", color="Sentimento", text="Percentual",
                      color_discrete_map={"Positivo":"#10B981","Neutro":"#64748B","Negativo":"#EF4444"})
    st.plotly_chart(fig_sent, use_container_width=True)

    st.divider()

    # 4. Nuvem de Palavras
    st.subheader("☁️ Nuvem de Palavras")
    texto_nuvem = " ".join(df[col_coment].astype(str).tolist())
    if texto_nuvem.strip():
        wc = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(texto_nuvem)
        fig_wc, ax = plt.subplots(); ax.imshow(wc, interpolation='bilinear'); ax.axis('off')
        st.pyplot(fig_wc)

    # 5. CHAT RAG LOCAL (Persistente e Rigoroso)
    st.divider()
    st.subheader("💬 Converse com os Dados Carregados")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt_chat := st.chat_input("Ex: 'Qual a porcentagem de críticas à equipe vs ao artista?'"):
        st.session_state.messages.append({"role": "user", "content": prompt_chat})
        with st.chat_message("user"):
            st.markdown(prompt_chat)

        with st.chat_message("assistant"):
            # Enviando 150 comentários para o chat para maior precisão de contagem
            dados_locais = "\n".join(df[col_coment].astype(str).head(150).tolist())
            
            prompt_rag_final = f"""
            Você é um assistente RAG local. 
            IGNORE BUSCAS NA INTERNET NESTE CHAT. Use APENAS os dados abaixo.
            
            DADOS DOS COMENTÁRIOS:
            {dados_locais}
            
            PERGUNTA: {prompt_chat}
            
            Se pedirem contagens ou porcentagens, baseie-se estritamente nos comentários listados acima.
            """
            
            response = client.chat.completions.create(
                model=MODELO_RAG, # sonar focado em contexto local
                messages=[
                    {"role": "system", "content": "Você é um analista de dados restrito aos comentários fornecidos. Não cite informações externas."},
                    {"role": "user", "content": prompt_rag_final}
                ]
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

else:
    st.info("👋 Por favor, carregue o arquivo CSV para iniciar.")

st.write("---")

col1, col2 = st.columns([1, 4])

with col1:
    try:
        rodape_image = Image.open('habbla_rodape.jpg')
        st.image(rodape_image, width=110)
    except FileNotFoundError:
        st.write("Logo rodapé não encontrada.")

with col2:
    st.markdown(
        """
        <div style='font-size: 12px; color: gray;'>
            Desenvolvido pela equipe de dados da <b>Habbla</b> | © 2026 Habbla Marketing<br>
            Versão 1.0.0 | Atualizado em: Janeiro/2026<br>
            <a href="mailto:nil@habbla.ai">nil@habbla.ai</a> |
            <a href="https://vybbe.com.br" target="_blank">Site Institucional</a>
        </div>
        """,
        unsafe_allow_html=True
    )