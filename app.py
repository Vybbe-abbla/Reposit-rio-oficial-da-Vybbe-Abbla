import streamlit as st
from datetime import datetime, timedelta, time

# Importações das suas APIs
from api_perplexity import buscar_noticias
from api_spotify import buscar_artista_spotify
from whatsapp_utils import montar_mensagem_whatsapp

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monitor de Notícias de Artistas", layout="wide")

# --- CSS CUSTOMIZADO ---
def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Banner Verde Superior */
        .top-banner {
            background-color: #16a34a;
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-block;
            margin-bottom: 0.5rem;
        }

        /* Estilização das Imagens */
        img {
            border-radius: 15px !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
            border: 2px solid #e5e7eb;
            object-fit: cover;
        }
        
        img:hover {
            transform: scale(1.03);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2) !important;
            border-color: #16a34a !important;
        }

        /* Botão Personalizado - Ajustado para Streamlit Cloud */
        div.stButton > button {
            width: 100% !important;
            border-radius: 8px !important;
            border: 1px solid #d1d5db !important;
            background-color: #f9fafb !important;
            color: #374151 !important;
            font-weight: 600 !important;
            padding: 0.5rem !important;
            height: 45px !important;
            transition: all 0.2s ease !important;
        }
        
        div.stButton > button:hover {
            background-color: #16a34a !important;
            color: white !important;
            border-color: #16a34a !important;
        }

        /* CARD DE NOTÍCIAS - FIX PARA MODO ESCURO */
        .news-card {
            background-color: #ffffff !important;
            padding: 1.2rem;
            border-radius: 8px;
            border-left: 6px solid #16a34a;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: left;
        }

        .news-card strong, 
        .news-card p {
            color: #111827 !important; 
            margin: 8px 0 !important;
            display: block;
        }

        .news-card a {
            color: #16a34a !important;
            font-weight: 700;
            text-decoration: none;
        }

        .news-card a:hover {
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO PARA CORRIGIR EXIBIÇÃO DE JSON ---
def tratar_dados_api(dados):
    """Extrai os campos necessários se a API retornar um dicionário bruto."""
    resumo = ""
    noticias = []
    
    if isinstance(dados, dict):
        resumo = dados.get("resumo_geral", "")
        noticias = dados.get("noticias", [])
    elif isinstance(dados, tuple) and len(dados) >= 2:
        resumo, noticias = dados[0], dados[1]
    else:
        resumo = str(dados)
        
    return resumo, noticias

# --- INICIALIZAÇÃO DO ESTADO ---
def init_session_state():
    if "artistas" not in st.session_state:
        st.session_state["artistas"] = [
            "Xand Avião", "NATTAN", "Avine Vinny", "Léo Foguete", "Felipe Amorim",
            "Zé Cantor", "Jonas Esticado", "Guilherme Dantas", "Manim Vaqueiro",
            "Mari Fernandez", "Zé Vaqueiro", "Talita Mel", "Lipe Lucena",
        ]
    if "data_inicio" not in st.session_state:
        hoje = datetime.today().date()
        st.session_state["data_fim"] = hoje
        st.session_state["data_inicio"] = hoje - timedelta(days=1)
    if "resumos_cache" not in st.session_state:
        st.session_state["resumos_cache"] = {}
    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = "painel"
    if "mensagem_whatsapp" not in st.session_state:
        st.session_state["mensagem_whatsapp"] = ""

# --- PÁGINAS ---
def pagina_configuracoes():
    st.sidebar.subheader("Configurações")
    preset = st.sidebar.selectbox(
        "Período de busca:",
        ["Últimas 24 horas", "Últimos 7 dias", "Último mês", "Personalizado"],
        index=0,
    )
    hoje = datetime.today().date()
    if preset == "Personalizado":
        data_inicio = st.sidebar.date_input("Início", st.session_state["data_inicio"])
        data_fim = st.sidebar.date_input("Fim", st.session_state["data_fim"])
    elif preset == "Últimos 7 dias":
        data_fim, data_inicio = hoje, hoje - timedelta(days=7)
    elif preset == "Último mês":
        data_fim, data_inicio = hoje, hoje - timedelta(days=30)
    else:
        data_fim, data_inicio = hoje, hoje - timedelta(days=1)

    st.session_state["data_inicio"], st.session_state["data_fim"] = data_inicio, data_fim
    st.sidebar.info(f"📅 {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}")

def pagina_principal():
    st.markdown('<div class="top-banner">Painel de artistas</div>', unsafe_allow_html=True)
    st.title("Artistas em Destaque")
    st.write("Acompanhe as últimas notícias e menções dos seus artistas favoritos.")

    artistas = st.session_state["artistas"]
    cols = st.columns(3)

    for idx, artista in enumerate(artistas):
        col = cols[idx % 3]
        with col:
            st.subheader(artista)
            try:
                imagem_url, _ = buscar_artista_spotify(artista)
            except:
                imagem_url = None

            if imagem_url:
                st.image(imagem_url, use_container_width=True)
            else:
                st.info("Imagem não encontrada.")

            # use_container_width garante que o botão preencha o card no Cloud
            if st.button(f"Ver notícias de {artista}", key=f"btn_{artista}", use_container_width=True):
                st.session_state["artista_selecionado"] = artista
                st.session_state["pagina_atual"] = "artista"
                st.rerun()

def pagina_artista():
    artista = st.session_state.get("artista_selecionado")
    
    if st.button("⬅️ Painel de artistas", use_container_width=True):
        st.session_state["pagina_atual"] = "painel"
        st.rerun()

    st.write("---")
    st.markdown(f"### {artista}")

    try:
        imagem_url, spotify_url = buscar_artista_spotify(artista)
    except:
        imagem_url, spotify_url = None, None

    if imagem_url:
        st.image(imagem_url, width=300)
    
    if spotify_url:
        st.markdown(f"[Ver artista no Spotify]({spotify_url})")

    st.markdown("---")
    
    dt_i = datetime.combine(st.session_state["data_inicio"], time.min)
    dt_f = datetime.combine(st.session_state["data_fim"], time.max)
    
    cache_key = (artista, str(dt_i), str(dt_f))
    if cache_key in st.session_state["resumos_cache"]:
        resumo, noticias = st.session_state["resumos_cache"][cache_key]
    else:
        with st.spinner("Buscando notícias..."):
            dados_brutos = buscar_noticias(artista, dt_i, dt_f)
            # CORREÇÃO: Trata os dados para não exibir o JSON
            resumo, noticias = tratar_dados_api(dados_brutos)
            st.session_state["resumos_cache"][cache_key] = (resumo, noticias)

    st.markdown("#### Resumo das principais menções")
    st.write(resumo if resumo else "Sem informações para este período.")

    st.markdown("#### Lista de notícias e posts")
    if noticias:
        for n in noticias:
            st.markdown(f"""
                <div class="news-card">
                    <strong>{n.get('titulo','Sem título')}</strong>
                    <p>{n.get('descricao', n.get('description', ''))}</p>
                    <a href="{n.get('url','#')}" target="_blank">Link para a fonte</a>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Nenhuma notícia encontrada.")

def secao_whatsapp():
    st.markdown("### Preparar resumo para WhatsApp")
    
    artistas = st.session_state["artistas"]
    dt_i = datetime.combine(st.session_state["data_inicio"], time.min)
    dt_f = datetime.combine(st.session_state["data_fim"], time.max)

    if st.button("Gerar mensagem consolidada", use_container_width=True):
        resumos_por_artista = {}
        links_por_artista = {}

        with st.spinner("Gerando resumos para todos os artistas..."):
            for artista in artistas:
                cache_key = (artista, str(dt_i), str(dt_f))
                if cache_key in st.session_state["resumos_cache"]:
                    resumo, noticias = st.session_state["resumos_cache"][cache_key]
                else:
                    try:
                        dados = buscar_noticias(artista, dt_i, dt_f)
                        resumo, noticias = tratar_dados_api(dados)
                        st.session_state["resumos_cache"][cache_key] = (resumo, noticias)
                    except:
                        resumo, noticias = "Erro na busca", []

                resumos_por_artista[artista] = resumo
                links_por_artista[artista] = [
                    {"titulo": n.get("titulo", ""), "url": n.get("url", "")}
                    for n in noticias if n.get("url")
                ]

            mensagem = montar_mensagem_whatsapp(
                resumos_por_artista, 
                links_por_artista,
                st.session_state["data_inicio"],
                st.session_state["data_fim"]
            )
    if st.session_state.get("mensagem_whatsapp"):
        st.text_area("Copie e cole no seu grupo de WhatsApp:", 
                     value=st.session_state["mensagem_whatsapp"], height=350)

def main():
    apply_custom_css()
    init_session_state()
    pagina_configuracoes()

    if st.session_state["pagina_atual"] == "artista":
        pagina_artista()
    else:
        pagina_principal()

    st.markdown("---")
    secao_whatsapp()

if __name__ == "__main__":
    main()