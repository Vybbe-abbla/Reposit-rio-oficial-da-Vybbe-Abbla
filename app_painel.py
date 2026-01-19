import streamlit as st
from PIL import Image

# Configuração inicial da página
st.set_page_config(
    page_title="Hub de Aplicações | Habbla",
    page_icon="🎯",
    layout="wide",
)

def local_css():
    st.markdown("""
        <style>
        /* Importação de fonte moderna */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Container dos Cards */
        .main-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px 0px;
        }

        /* Estilização do Card */
        .card {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 30px;
            text-align: left;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease-in-out;
            border: 1px solid #f0f2f6;
            height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            text-decoration: none !important;
            color: inherit !important;
        }

        /* Efeito Hover */
        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0 12px 20px rgba(0, 0, 0, 0.1);
            border-color: #ff4b4b; /* Cor de destaque Vybbe/Streamlit */
        }

        .card-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }

        .card-title {
            font-weight: 800;
            font-size: 1.4rem;
            color: #1f1f1f;
            margin-bottom: 10px;
        }

        .card-description {
            font-size: 0.95rem;
            color: #5e5e5e;
            line-height: 1.5;
        }

        /* Link invisível que cobre o card todo */
        .card-link {
            text-decoration: none;
        }
        
        /* Ajuste para modo escuro do Streamlit */
        @media (prefers-color-scheme: dark) {
            .card {
                background-color: #1e1e1e;
                border-color: #333;
            }
            .card-title { color: #ffffff; }
            .card-description { color: #bcbcbc; }
        }
        </style>
    """, unsafe_allow_html=True)

def create_card(icon, title, description, link):
    """Gera o HTML para um card clicável"""
    card_html = f"""
        <a href="{link}" target="_blank" class="card-link">
            <div class="card">
                <div>
                    <div class="card-icon">{icon}</div>
                    <div class="card-title">{title}</div>
                    <div class="card-description">{description}</div>
                </div>
            </div>
        </a>
    """
    return card_html

def main():
    local_css()

    image = Image.open('habbla_rodape.jpg')
    st.image(image, width=110)

    # Cabeçalho do Painel
    st.title("🎯 Central de Inteligência")
    st.markdown("Bem-vindo ao hub de navegação. Selecione uma ferramenta abaixo para começar.")
    st.divider()

    # Definição dos dados dos cards
    cards_data = [
        {
            "icon": "📊",
            "title": "Charts",
            "description": "Rankings de músicas, artistas e álbuns mais populares.", 
            "link": "https://vybbestreams.streamlit.app/"
        },
        {
            "icon": "🎧",
            "title": "Popularidade Spotify",
            "description": "Analytics detalhado sobre o desempenho e alcance dos artistas na plataforma.",
            "link": "https://vybbe-habbla-analytics-spotify.streamlit.app/"
        },
        {
            "icon": "📰",
            "title": "Monitoramento de Notícias",
            "description": "Monitoramento diário de notícias sobre os artistas da Vybbe..",
            "link": "https://noticias-artistas.streamlit.app/"
        },
        {
            "icon": "🚨",
            "title": "Monitoramento de Crise",
            "description": "Gestão de imagem e criação de relatórios estratégicos para situações críticas.",
            "link": "https://painel-crise.streamlit.app/"
        }
    ]


    cols = st.columns(2) # Grid 2x2 para telas maiores

    for idx, card in enumerate(cards_data):
        with cols[idx % 2]:
            st.markdown(create_card(
                card['icon'], 
                card['title'], 
                card['description'], 
                card['link']
            ), unsafe_allow_html=True)

    # Rodapé elegante
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

if __name__ == "__main__":
    main()