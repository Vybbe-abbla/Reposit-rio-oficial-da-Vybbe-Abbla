import streamlit as st
import pandas as pd
import io
import os
import re
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Definição de Caminhos e Configurações
# -----------------------------------------------------------------------------
ARTISTS_FILE_PATH = "tabela_artistas.xlsx"
MUSIC_PLATFORMS_FILE_PATH = "1.Streamings.xlsx"

# Dicionário de configuração para a geração dos arquivos de download
DOWNLOAD_CONFIG = {
    "Spotify_Daily": {
        "file_name": "spotify_daily_filtered_data.xlsx",
        "sheets": {
            "Brasil - Top Songs Daily": "Brasil - Top Songs Daily",
            "Brasil - Top Artists Daily": "Brasil - Top Artists Daily",
            "Brasil - Top Viral Daily": "Brasil - Top Viral Daily",
            "Global - Top Songs Daily": "Global - Top Songs Daily",
            "Global - Top Artists Daily": "Global - Top Artists Daily",
            "Global - Top Viral Daily": "Global - Top Viral Daily"
        }
    },
    "Spotify_Weekly": {
        "file_name": "spotify_weekly_filtered_data.xlsx",
        "sheets": {
            "Brasil - Top Songs Weekly": "Brasil - Top Songs Weekly",
            "Brasil - Top Artists Weekly": "Brasil - Top Artists Weekly",
            "Brasil - Top Albums Weekly": "Brasil - Top Albums Weekly",
            "Global - Top Songs Weekly": "Global - Top Songs Weekly",
            "Global - Top Artists Weekly": "Global - Top Artists Weekly",
            "Global - Top Album Weekly": "Global - Top Album Weekly"
        }
    },
    "Youtube": {
        "file_name": "youtube_filtered_data.xlsx",
        "sheets": {
            "Youtube - Daily Videos": "Youtube - Daily Videos",
            "Youtube - Daily Shorts": "Youtube - Daily Shorts",
            "Youtube - Weekly Music": "Youtube - Weekly Music",
            "Youtube - Weekly Artists": "Youtube - Weekly Artists"
        }
    },
    "Outras Plataformas": {
        "file_name": "other_platforms_filtered_data.xlsx",
        "sheets": {
            "Deezer": "Deezer",
            "Amazon": "Amazon",
            "Apple": "Apple"
        }
    }
}

# -----------------------------------------------------------------------------
# Funções Auxiliares
# -----------------------------------------------------------------------------

@st.cache_data
def load_artist_data(file_path):
    """
    Carrega a lista de artistas de um arquivo Excel e armazena em cache.
    Isso evita que o Streamlit recarregue o arquivo a cada interação.
    """
    try:
        df = pd.read_excel(file_path, sheet_name='tabela_artistas')
        return df['Artista'].str.strip().tolist()
    except FileNotFoundError:
        st.error(f"Erro: O arquivo de artistas '{file_path}' não foi encontrado.")
        st.stop()
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo de artistas: {e}")
        st.stop()
    
def normalize_string(s):
    """Normaliza uma string para busca, removendo acentuação e convertendo para minúsculas."""
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[áàâãäÁÀÂÃÄ]", "a", s)
    s = re.sub(r"[éèêëÉÈÊË]", "e", s)
    s = re.sub(r"[íìîïÍÌÎÏ]", "i", s)
    s = re.sub(r"[óòôõöÓÒÔÕÖ]", "o", s)
    s = re.sub(r"[úùûüÚÙÛÜ]", "u", s)
    s = s.replace("ç", "c")
    return s

def filter_by_artist(df, artist_list):
    """
    Filtra um DataFrame com base nos artistas da lista de referência.
    A busca é case-insensitive e ignora acentuação.
    """
    artist_cols = ['artist_names', 'artist_name', 'Artista', 'Artistas']
    found_col = next((col for col in artist_cols if col in df.columns), None)

    if not found_col:
        return pd.DataFrame()

    normalized_artist_list = [normalize_string(artist) for artist in artist_list]
    
    mask = df[found_col].apply(
        lambda x: any(normalized_artist in normalize_string(str(x)) for normalized_artist in normalized_artist_list)
    )
    return df[mask]

# -----------------------------------------------------------------------------
# Layout do Aplicativo Streamlit
# -----------------------------------------------------------------------------
st.title("Análise de Dados de Artistas por Período")

# Carregar a lista de artistas uma única vez
artist_list = load_artist_data(ARTISTS_FILE_PATH)

st.sidebar.title("Navegação")
# A navegação foi simplificada para processar todos os arquivos automaticamente
st.sidebar.write("Todos os dados serão processados e estarão disponíveis para download em categorias separadas.")

if st.sidebar.button('Clique para Atualizar'):
    st.sidebar.write('Atualizando...')
    st.rerun()

st.sidebar.write(f'A página foi carregada em: {st.session_state.get("start_time", "Não definido")}')

# Você pode usar a session_state para demonstrar que a página recarrega
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = st.session_state.get('start_time', st.session_state.get('start_time', 'Agora mesmo'))


# -----------------------------------------------------------------------------
# Processamento e Exibição dos Dados
# -----------------------------------------------------------------------------
all_filtered_dfs = {
    "Spotify_Daily": {},
    "Spotify_Weekly": {},
    "Youtube": {},
    "Outras Plataformas": {}
}
data_found = False

if not os.path.exists(MUSIC_PLATFORMS_FILE_PATH):
    st.warning(f"O arquivo de plataformas de música '{MUSIC_PLATFORMS_FILE_PATH}' não foi encontrado.")
else:
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%d/%m/%Y')

    for category, config in DOWNLOAD_CONFIG.items():
        st.subheader(f"Processando dados: {category}")
        for sheet_title, sheet_name in config["sheets"].items():
            try:
                df = pd.read_excel(MUSIC_PLATFORMS_FILE_PATH, sheet_name=sheet_name, engine='openpyxl')
                
                df.insert(0, 'Data', yesterday_str)

                if 'Data de pico' in df.columns:
                    df['Data de pico'] = pd.to_datetime(df['Data de pico'], errors='coerce').dt.strftime('%d/%m/%Y')
                
                filtered_df = filter_by_artist(df, artist_list)
                
                if not filtered_df.empty:
                    st.write(f"Dados encontrados para: **{sheet_title}**")
                    all_filtered_dfs[category][sheet_title] = filtered_df
                    data_found = True
                else:
                    # Mensagem específica para os rankings globais do Spotify
                    if sheet_name in ["Global - Top Songs Daily", "Global - Top Artists Daily", "Global - Top Viral Daily",
                                      "Global - Top Songs Weekly", "Global - Top Artists Weekly", "Global - Top Album Weekly"]:
                        st.info(f"Nenhum artista da sua lista (Vybee) foi encontrado nos dados globais de '{sheet_title}'.")
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a planilha '{sheet_name}': {e}")
    
    if not data_found:
        st.info("Nenhum dado de artista da sua lista foi encontrado nas planilhas selecionadas.")

# -----------------------------------------------------------------------------
# Seção de Download
# -----------------------------------------------------------------------------
st.subheader("Download dos Dados Filtrados")

downloads_generated = False
for category, config in DOWNLOAD_CONFIG.items():
    dfs_to_download = all_filtered_dfs.get(category)
    if dfs_to_download:
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for name, df in dfs_to_download.items():
                    if not df.empty:
                        sheet_name = re.sub(r'[^a-zA-Z0-9_]+', '', name.replace(' ', '_').replace('-', '_'))[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            st.download_button(
                label=f"Baixar Dados de {category.replace('_', ' ')}",
                data=output.getvalue(),
                file_name=config["file_name"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            downloads_generated = True
        except NameError:
            st.error("Erro: A biblioteca 'xlsxwriter' não está instalada. Por favor, instale-a.")
            st.stop()
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o arquivo Excel para {category}: {e}")

if not downloads_generated:
    st.write("Nenhum dado filtrado para download.")


