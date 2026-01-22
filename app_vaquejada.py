import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# Configuração da página para modo Wide
st.set_page_config(page_title="Relatório BYD Vaquejada", layout="wide")

# CSS Customizado para Identidade Preto, Amarelo e Branco
st.markdown("""
<style>
    .main { background-color: #ffffff; color: #000000; }
    [data-testid="stAppViewContainer"] { background-color: #ffffff; }
    
    /* Estilização dos Blocos */
    .section-container {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 30px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .kpi-card {
        background-color: #000000;
        color: #ffdf00; /* Amarelo */
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    
    h1, h2, h3 { color: #000000; font-weight: 800; }
    .highlight-yellow { color: #d97706; font-weight: bold; }
    
    /* Tabelas e Listas */
    .stDataFrame { border: 1px solid #ffdf00; }
    .vybbe-title { color: #000000; border-left: 5px solid #ffdf00; padding-left: 15px; font-size: 24px; }
    .check-icon { color: #ffdf00; font-weight: bold; margin-right: 10px; }
</style>
""", unsafe_allow_html=True)

# 1. Carregamento e Processamento de Dados
@st.cache_data
def load_data():
    df = pd.read_excel("Vaquejada.xlsx")
    cols = ['Engaxamento total', 'Total comentarios', 'Compartilhamento']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

rodape_image = Image.open('habbla_rodape.jpg')
st.image(rodape_image, width=110)
# --- HEADER ---
st.title("🏇 Relatório de Impacto: Circuito BYD de Vaquejada")
st.write("Análise detalhada de redes sociais e engajamento estratégico.")

# --- 1. CARDS DE MÉTRICAS (KPIs) ---
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card"><h3>{df["Engaxamento total"].sum():,.0f}</h3><p>Engajamento Total</p></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><h3>{df["Total comentarios"].sum():,.0f}</h3><p>Comentários</p></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><h3>{df["Compartilhamento"].sum():,.0f}</h3><p>Compartilhamentos</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 2. GRÁFICO DE PIZZA + ANÁLISE DETALHADA ---
st.markdown("### 📊 Análise de Sentimento")
col_pie, col_sent_text = st.columns([1, 1])

with col_pie:
    labels = ['Positivo', 'Neutro', 'Dúvidas']
    values = [72, 18, 10]
    fig_pie = px.pie(names=labels, values=values, 
                     color_discrete_sequence=['#ffdf00', '#333333', '#e5e7eb'],
                     hole=0.4)
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_sent_text:
    st.markdown("#### Detalhamento do Sentimento")
    st.write("A maior parte do público reagiu de forma entusiástica ao anúncio, especialmente pela magnitude da premiação.")
    
    st.markdown("""
    - **Positivo (72%)**: Usuários celebrando a união da tradição com a tecnologia BYD.
    - **Neutro (18%)**: Marcações de amigos e compartilhamentos diretos sem comentário textual.
    - **Dúvidas (10%)**: Questionamentos técnicos sobre o regulamento e acesso à Arena.
    """)
    
    st.info("**Exemplos de Comentários:**\n\n"
            "💬 *'A vaquejada subiu de nível com a BYD! 🚀'*\n\n"
            "💬 *'Arena Pernambuco vai ficar pequena para esse evento.'*\n\n"
            "💬 *'Como faz para inscrever o cavalo? Premiação histórica!'*")

# --- 3. GRÁFICO DE ENGAJAMENTO (COLUNA ÚNICA) ---
st.markdown("### 📈 Engajamento por Redes Sociais")
eng_social = df.groupby('Rede Social')['Engaxamento total'].sum().reset_index().sort_values('Engaxamento total', ascending=False)
fig_bar = px.bar(eng_social, x='Rede Social', y='Engaxamento total',
                 color_discrete_sequence=['#000000'])
fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig_bar, use_container_width=True)

# --- 4. LINKS DAS PÁGINAS ---
st.markdown("### 🔗 Links de Maior Relevância")
st.dataframe(df[['Link', 'Rede Social', 'Engaxamento total']].sort_values(by='Engaxamento total', ascending=False).head(8), 
             use_container_width=True, hide_index=True)

# --- 5. PAPEL DA VYBBE (ESTRUTURA IMAGEM 2) ---
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.markdown('<p class="vybbe-title">Papel da Vybbe no Lançamento</p>', unsafe_allow_html=True)

v1, v2 = st.columns(2)
with v1:
    st.markdown("**Posicionamento**")
    st.write("Sócia estratégica do Circuito BYD, atuando na gestão de carreira de artistas e eventos.")
with v2:
    st.markdown("**Atuação**")
    st.write("Gestão de artistas, produção de eventos e coordenação de parcerias estratégicas.")

st.markdown("**Artistas Vybbe Envolvidos**")
st.write("Xand Avião • Zé Vaqueiro • Mari Fernandez • Felipe Amorim • Léo Foguete • Nattan")

st.markdown("**Impacto da Vybbe**")
st.markdown("""
- Contribuição significativa ao alcance do evento através de seus artistas.
- Mencionada em parcerias estratégicas ao lado de **@xandaviao** e **@_topeventos**.
- Amplia alcance do evento através de sua rede de artistas (**182K+ seguidores**).
- Reforça posicionamento como gestora de eventos de grande impacto.
""")
st.markdown('</div>', unsafe_allow_html=True)

# --- 6. DETALHES DO EVENTO (FINAL DA PÁGINA) ---
st.markdown('<div class="section-container" style="background-color: #000000; color: #ffffff;">', unsafe_allow_html=True)
st.markdown('<h2 style="color: #ffdf00;">Detalhes do Evento</h2>', unsafe_allow_html=True)

d1, d2 = st.columns(2)
with d1:
    st.markdown("<h4 style='color: #ffdf00;'>Informações Gerais</h4>", unsafe_allow_html=True)
    st.markdown("""
    **Nome:** Circuito Nacional BYD de Vaquejada  
    **Data do Lançamento:** 19 de janeiro de 2026  
    **Local da Final:** Arena Pernambuco  
    **Premiação:** R$ 12+ milhões  
    **Veículos em Jogo:** 70+
    """)

with d2:
    st.markdown("<h4 style='color: #ffdf00;'>Destaques</h4>", unsafe_allow_html=True)
    highlights = [
        "Primeira final de vaquejada em estádio de futebol",
        "Maior premiação do circuito",
        "Participação de artistas renomados",
        "Cobertura em múltiplas plataformas"
    ]
    for h in highlights:
        st.markdown(f" {h}")
st.markdown('</div>', unsafe_allow_html=True)


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

st.caption("© 2026 Relatório Executivo BYD - Gerado em 22 de Janeiro")