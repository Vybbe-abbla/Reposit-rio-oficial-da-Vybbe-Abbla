import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="Relatório BYD Vaquejada", layout="wide")

# Estilização para Cards
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.title("📊 Relatório de Social Listening e Reputação de Marca")
st.subheader("Circuito Nacional BYD de Vaquejada – Grande Final")
st.write("**Data da Análise:** 21 de Janeiro de 2026 | **Amostra:** 4.045 Comentários")

st.divider()

# --- 1. CARDS INFORMATIVOS (RESUMO EXECUTIVO) ---
st.header("1. Resumo Executivo")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card"><b>Total de Comentários</b><br><h2>4.045</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><b>Páginas Monitoradas</b><br><h2>14</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><b>Sentimento Positivo</b><br><h2>62%</h2></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="metric-card"><b>Status de Marca</b><br><h2>Forte</h2></div>', unsafe_allow_html=True)

st.divider()

# --- 2. CONTEXTO E METODOLOGIA ---
st.header("2. Contexto e Metodologia")
st.write("""
Este dashboard analisa a repercussão estratégica do anúncio da final do **Circuito Nacional BYD de Vaquejada** na Arena de Pernambuco. 
A análise foi realizada através de *Social Listening* qualitativo e quantitativo, processando o engajamento de influenciadores, 
portais e lideranças políticas. O foco está na percepção da marca BYD e na aceitação da Arena como palco inédito do esporte.
""")

st.divider()

# --- 3. ANÁLISE DE SENTIMENTO (PLOTLY EXPRESS) ---
st.header("3. Análise de Sentimento")

# Dados de Sentimento
sentiment_data = {
    "Sentimento": ["Positivo", "Neutro", "Negativo"],
    "Quantidade": [2508, 1011, 526],
    "Porcentagem": [62, 25, 13]
}
df_sentiment = pd.DataFrame(sentiment_data)

col_chart, col_text = st.columns([1, 1])

with col_chart:
    fig = px.pie(
        df_sentiment, 
        values='Quantidade', 
        names='Sentimento',
        color='Sentimento',
        color_discrete_map={'Positivo':'#28a745', 'Neutro':'#ffc107', 'Negativo':'#dc3545'},
        hole=0.4,
        title="Distribuição Geral de Sentimento"
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col_text:
    st.write("### Drivers de Percepção")
    st.markdown("""
    * **Positivo (62%):** Celebrando o ineditismo da Arena e o prestígio da marca **BYD**. O apoio de **Wesley Safadão** é o principal validador.
    * **Neutro (25%):** Concentra o maior volume de dúvidas logísticas (preços, datas e acesso). Indica alta intenção de compra.
    * **Negativo (13%):** Focado em preocupações com o gramado da Arena e reações à polarização política.
    """)

st.divider()

# --- 4. ANÁLISE POR PÁGINA ---
st.header("4. Detalhamento por Canal / Página")

# Dados da Tabela
page_data = [
    [1, "@caiolima_of", 1185, "https://www.instagram.com/reel/DTtmCRCjItX/"],
    [2, "@doidimporvaquejada", 214, "https://www.instagram.com/reel/DTu17-uDpVL/"],
    [3, "@caiolima_of", 116, "https://www.instagram.com/reel/DTtr0MGjG94/"],
    [4, "@x1vaquejadanoticias", 123, "https://www.instagram.com/p/DQxfKIICTwg/"],
    [5, "@mangabinhaa", 349, "https://www.instagram.com/reel/DTtji6aDTrV/"],
    [6, "@mangabinhaa", 140, "https://www.instagram.com/reel/DTtrK0HjP68/"],
    [7, "@circuitonacionalqm", 40, "https://www.instagram.com/reel/DTtaCwjkeMR/"],
    [8, "@_status_de_vaqueiro", 140, "https://www.instagram.com/reel/DTuqQp4kVtz/"],
    [9, "@preftvoficial", 555, "https://www.instagram.com/reel/DTtkHx_DZ6p/"],
    [10, "@portaldascidadespe_", 283, "https://www.instagram.com/reel/DTtnx-Jjseb/"],
    [11, "@henriquequeirozfilho.pe", 281, "https://www.instagram.com/reel/DTtmOmBjiNE/"],
    [12, "@doidimporvaquejada", 105, "https://www.instagram.com/reel/DTtV26cDoAs/"],
    [13, "@portaldeprefeitura", 415, "https://www.instagram.com/reel/DTuv9zjDZkg/"],
    [14, "@mangabinhaa", 99, "https://www.instagram.com/reel/DTtZTlbDjS4/"]
]

df_pages = pd.DataFrame(page_data, columns=["ID", "Página/Perfil", "Total Comentários", "Link Direto"])

# Exibição da Tabela
st.dataframe(
    df_pages, 
    column_config={
        "Link Direto": st.column_config.LinkColumn("Link da Publicação")
    },
    use_container_width=True,
    hide_index=True
)

st.divider()

# --- 5. INSIGHTS ESTRATÉGICOS ---
st.header("5. Insights e Recomendações")
st.info("**Destaque:** O perfil @caiolima_of detém o maior share of voice orgânico do projeto.")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Oportunidades")
    st.markdown("""
    - **Conversão de Leads:** Criar FAQ para os 25% neutros.
    - **Brand Equity:** Ativações de Test-Drive BYD na Arena.
    - **Expansão:** Usar o canal do Safadão para venda de ingressos VIP.
    """)
with col_b:
    st.subheader("Mitigação de Riscos")
    st.markdown("""
    - **Gestão de Infra:** Comunicado sobre proteção do gramado.
    - **Despolitização:** Focar o discurso no esporte e inovação.
    - **SAC Proativo:** Responder dúvidas técnicas nos 14 canais.
    """)

st.divider()

# --- 6. CONCLUSÃO ---
st.header("6. Conclusão Executiva")
st.success("""
O lançamento atingiu um volume crítico de engajamento (4.045 menções), consolidando a BYD como uma marca inovadora no contexto regional. 
A recepção positiva de 62% valida a estratégia de locação e embaixadores. Recomenda-se o início imediato da fase de vendas para aproveitar 
o buzz gerado.
""")

st.write("---")
st.caption("Relatório Gerado por Inteligência de Social Listening - 2026")