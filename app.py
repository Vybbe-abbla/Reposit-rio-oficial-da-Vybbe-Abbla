import streamlit as st
from datetime import datetime, timedelta, time
from api_perplexity import buscar_noticias
from api_spotify import buscar_artista_spotify
from whatsapp_utils import montar_mensagem_whatsapp

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monitor de Notícias de Artistas", layout="wide")

def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .top-banner {
            background-color: #FFA500;
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-block;
            margin-bottom: 0.5rem;
        }
    
        /* Imagens com bordas arredondadas e espaçamento inferior para os botões */
        .img-painel {
            border-radius: 15px !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
            border: 2px solid #e5e7eb;
            object-fit: cover;
            width: 100%;
            margin-bottom: 15px; /* Ajuste para não colar no botão */
        }
        .img-painel:hover {
            transform: scale(1.03);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2) !important;
            border-color: #FFD700 !important;
        }

        /* Foto circular para Segmentação */
        .circular-img-config {
            width: 150px;
            height: 150px;
            border-radius: 50% !important;
            object-fit: cover;
            border: 2px solid #1C1C1C;
        }

        /* Botão com estilo original e espaçamento */
        div.stButton > button {
            width: 100% !important;
            border-radius: 8px !important;
            border: 1px solid #d1d5db !important;
            background-color: #f9fafb !important;
            color: #374151 !important;
            font-weight: 600 !important;
            padding: 0.5rem !important;
            height: 45px !important;
            margin-top: 5px; /* Garante distância da imagem */
        }
        div.stButton > button:hover {
            background-color: #FFA500 !important;
            color: white !important;
            border-color: #FFA500 !important;
        }

        .news-card {
            background-color: #ffffff !important;
            padding: 1.2rem;
            border-radius: 8px;
            border-left: 6px solid #16a34a;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #111827 !important;
        }
        /* Ajuste de distância solicitado para a página de segmentação */
        .spacer-segmentacao {
            margin-top: 40px;
        }

        /* Estilo para o botão de salvar específico */
        .btn-salvar-container {
            margin-top: -15px;
            margin-bottom: 20px;
        }
                
        </style>
    """, unsafe_allow_html=True)

def init_session_state():
    if "artistas" not in st.session_state:
        st.session_state["artistas"] = ["Xand Avião", "NATTAN", "Avine Vinny", "Léo Foguete", "Felipe Amorim", "Zé Cantor", "Jonas Esticado", "Guilherme Dantas", "Manim Vaqueiro", "Mari Fernandez", "Zé Vaqueiro", "Talita Mel", "Lipe Lucena"]
    if "pagina_atual" not in st.session_state: st.session_state["pagina_atual"] = "painel"
    if "palavras_chaves" not in st.session_state: st.session_state["palavras_chaves"] = {art: "" for art in st.session_state["artistas"]}
    if "data_inicio" not in st.session_state:
        hoje = datetime.today().date()
        st.session_state["data_fim"] = hoje
        st.session_state["data_inicio"] = hoje - timedelta(days=2)
    if "resumos_cache" not in st.session_state: st.session_state["resumos_cache"] = {}
    if "mensagem_whatsapp" not in st.session_state: st.session_state["mensagem_whatsapp"] = ""

def sidebar_configuracoes():
    # 1. Período de busca acima de tudo na sidebar
    st.sidebar.subheader("Período de busca")
    preset = st.sidebar.selectbox("Intervalo:", ["Últimas 48 horas", "Últimos 7 dias", "Personalizado"], index=0)
    
    hoje = datetime.today().date()
    if preset == "Personalizado":
        st.session_state["data_inicio"] = st.sidebar.date_input("Início", st.session_state["data_inicio"])
        st.session_state["data_fim"] = st.sidebar.date_input("Fim", st.session_state["data_fim"])
    elif preset == "Últimos 7 dias":
        st.session_state["data_inicio"], st.session_state["data_fim"] = hoje - timedelta(days=7), hoje
    else:
        st.session_state["data_inicio"], st.session_state["data_fim"] = hoje - timedelta(days=2), hoje

    st.sidebar.info(f"📅 {st.session_state['data_inicio'].strftime('%d/%m')} até {st.session_state['data_fim'].strftime('%d/%m/%Y')}")
    st.sidebar.markdown("---")
    st.sidebar.title("Configurações")
    
    # 2. Somente botão de segmentação (Painel Principal removido)
    if st.sidebar.button("⚙️ Segmentação", use_container_width=True):
        st.session_state["pagina_atual"] = "segmentacao"; st.rerun()

def pagina_segmentacao():
    st.markdown('<div class="top-banner">Segmentação Palavras-Chaves</div>', unsafe_allow_html=True)
    st.title("⚙️ Personalizar Termos de Busca")
    st.write("---")

    # 3. Aumentar distância entre título e imagens
    st.markdown('<div class="segmentacao-spacer"></div>', unsafe_allow_html=True)
    
    for artista in st.session_state["artistas"]:
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                try: img_url, _ = buscar_artista_spotify(artista)
                except: img_url = "https://via.placeholder.com/150"
                st.markdown(f'<img src="{img_url}" class="circular-img-config">', unsafe_allow_html=True)
                st.markdown(f'<p style="text-align: center; font-weight: bold; margin-top: 5px;">{artista}</p>', unsafe_allow_html=True)
            with col2:
                val = st.session_state["palavras_chaves"].get(artista, "")
                texto_input = st.text_area(f"Termos para {artista}:", value=val, key=f"seg_{artista}", height=70)
                
                # 4. Botão de salvar logo abaixo do text box
                if st.button(f"Salvar termos de {artista}", key=f"save_{artista}"):
                    st.session_state["palavras_chaves"][artista] = texto_input
                    st.success(f"Configuração salva para {artista}!")
        st.divider()
    
    if st.button("⬅️ Voltar ao Painel Principal", use_container_width=True):
        st.session_state["pagina_atual"] = "painel"; st.rerun()

def secao_whatsapp():
    st.markdown("---")
    st.markdown("### Preparar resumo para WhatsApp")
    dt_i = datetime.combine(st.session_state["data_inicio"], time.min)
    dt_f = datetime.combine(st.session_state["data_fim"], time.max)

    if st.button("Gerar mensagem consolidada", use_container_width=True):
        resumos_por_artista = {}
        links_por_artista = {}
        with st.spinner("Consolidando notícias..."):
            for artista in st.session_state["artistas"]:
                termos = st.session_state["palavras_chaves"].get(artista, "")
                # Chamada corrigida com 4 argumentos
                resumo, noticias = buscar_noticias(artista, dt_i, dt_f, termos)
                resumos_por_artista[artista] = resumo
                links_por_artista[artista] = [{"titulo": n.get("titulo"), "url": n.get("url")} for n in noticias if n.get("url")]

            st.session_state["mensagem_whatsapp"] = montar_mensagem_whatsapp(
                resumos_por_artista, links_por_artista, st.session_state["data_inicio"], st.session_state["data_fim"]
            )
    
    if st.session_state["mensagem_whatsapp"]:
        st.text_area("Copie para o WhatsApp:", value=st.session_state["mensagem_whatsapp"], height=300)

def pagina_principal():
    st.markdown('<div class="top-banner">Painel de artistas</div>', unsafe_allow_html=True)
    st.title("Artistas em Destaque")
    cols = st.columns(3)
    for idx, artista in enumerate(st.session_state["artistas"]):
        with cols[idx % 3]:
            st.subheader(artista)
            try: img_url, _ = buscar_artista_spotify(artista)
            except: img_url = None
            if img_url: st.markdown(f'<img src="{img_url}" class="img-painel">', unsafe_allow_html=True)
            if st.button(f"Ver notícias de {artista}", key=f"btn_{artista}"):
                st.session_state["artista_selecionado"] = artista
                st.session_state["pagina_atual"] = "artista"; st.rerun()
    secao_whatsapp()

def pagina_artista():
    artista = st.session_state.get("artista_selecionado")
    
    # Botão de voltar original
    if st.button("⬅️ Voltar ao Painel", use_container_width=True):
        st.session_state["pagina_atual"] = "painel"
        st.rerun()

    st.markdown("---")
    
    # --- BLOCO DA IMAGEM DO ARTISTA (Restaurado) ---
    try:
        # Busca imagem e link do Spotify conforme o arquivo original
        imagem_url, spotify_url = buscar_artista_spotify(artista)
    except:
        imagem_url, spotify_url = None, None

    if imagem_url:
        # Exibe a imagem com a classe CSS original (img-painel ou similar)
        st.markdown(f'<img src="{imagem_url}" class="img-painel" style="width:300px;">', unsafe_allow_html=True)
    
    if spotify_url:
        st.markdown(f"[Ver artista no Spotify]({spotify_url})")

    st.markdown(f"## Resultados: {artista}")
    
    # --- LÓGICA DE DATAS E BUSCA ---
    termos = st.session_state.get("palavras_chaves", {}).get(artista, "")
    dt_i = datetime.combine(st.session_state["data_inicio"], time.min)
    dt_f = datetime.combine(st.session_state["data_fim"], time.max)
    
    # Chave de cache para evitar redundância
    cache_key = (artista, str(dt_i), str(dt_f), termos)
    
    if cache_key in st.session_state["resumos_cache"]:
        resumo, noticias = st.session_state["resumos_cache"][cache_key]
    else:
        with st.spinner(f"Buscando notícias de {artista}..."):
            # Chama a função buscar_noticias com os 4 argumentos necessários
            resumo, noticias = buscar_noticias(artista, dt_i, dt_f, termos)
            st.session_state["resumos_cache"][cache_key] = (resumo, noticias)

    # --- EXIBIÇÃO DO CONTEÚDO (Layout Original) ---
    st.subheader("Resumo das Principais Menções")
    st.write(resumo if resumo else "Sem informações para este período.")

    st.markdown("---")
    st.subheader("Lista de notícias e posts")
    
    if noticias:
        for n in noticias:
            # Layout de card original usando a classe .news-card do seu CSS
            st.markdown(f"""
                <div class="news-card">
                    <strong>{n.get('titulo', 'Sem título')}</strong>
                    <p>{n.get('descricao', n.get('description', ''))}</p>
                    <a href="{n.get('url', '#')}" target="_blank">Link para a fonte</a>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Nenhuma notícia encontrada.")

def main():
    apply_custom_css()
    init_session_state()
    sidebar_configuracoes()

    atual = st.session_state["pagina_atual"]
    if atual == "segmentacao": pagina_segmentacao()
    elif atual == "artista": pagina_artista()
    else: pagina_principal()

if __name__ == "__main__":
    main()