import pandas as pd
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import plotly.express as px
from dotenv import load_dotenv
import os
import json 
import tempfile 
from PIL import Image

st.set_page_config(page_title='Vybbe Streams', layout="wide")

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração e Funções Globais (uma única vez) ---
# Pega o conteúdo da variável de ambiente como uma string
google_sheets_creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

# Verifica se a variável de ambiente existe
if not google_sheets_creds_json:
    st.error("A variável de ambiente GOOGLE_SHEETS_CREDENTIALS não foi encontrada.")
else:
    # Cria um arquivo JSON temporário a partir da string
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_creds_file:
        temp_creds_file.write(google_sheets_creds_json)
        temp_file_name = temp_creds_file.name

    # Autentica usando o arquivo JSON temporário
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(filename=temp_file_name, scopes=scopes)
        client = gspread.authorize(creds)
        planilha_completa = client.open(title="2025_Charts")
    except Exception as e:
        st.error(f"Erro ao autenticar com o Google Sheets: {e}")
        planilha_completa = None # Define como None em caso de falha

    # Deleta o arquivo temporário por segurança
    os.remove(temp_file_name)


# --- Função de Reuso da Lógica com a correção de Planilha Específica ---
@st.cache_data
def load_data(sheet_index):
    # Verifica se a planilha_completa foi carregada com sucesso
    if not planilha_completa:
        return pd.DataFrame()
    
    try:
        worksheet = planilha_completa.get_worksheet(sheet_index)

        if sheet_index == 5:
            expected_headers = ['DATA', 'Rank', 'uri', 'Artista', 'Música', 'source', 'peak_rank', 'previous_rank', 'days_on_chart', 'Corte charts', 'Data de Pico']
            data = worksheet.get_all_records(expected_headers=expected_headers)
        else:
            data = worksheet.get_all_records()

        df = pd.DataFrame(data)
        return df
    except gspread.exceptions.APIError as e:
        st.error(f"Erro ao acessar a planilha (sheet {sheet_index}): {e}")
        return pd.DataFrame()

# Obtém as credenciais do Spotify do ambiente
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))
except Exception as e:
    st.error(f"Erro ao autenticar com a API do Spotify: {e}")
    sp = None

@st.cache_data
def get_artist_image(artist_name):
    if sp is None:
        return None
    try:
        results = sp.search(q='artist:' + artist_name, type='artist', limit=1)
        if results['artists']['items'] and results['artists']['items'][0]['images']:
            return results['artists']['items'][0]['images'][0]['url']
    except Exception as e:
        st.error(f"Erro ao buscar imagem do artista {artist_name}: {e}")
    return None

def display_daily_chart(sheet_index, section_title, item_type, key_suffix, chart_filter_options):
    st.subheader(section_title)
    
    df = load_data(sheet_index)

    if not df.empty:
        item_col = 'Música' if 'Música' in df.columns else 'Artista'
        
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        date_col_name = 'DATA' if 'DATA' in df.columns else 'Data'
        
        df[date_col_name] = pd.to_datetime(df[date_col_name], format="%d/%m/%Y")
        
        df_yesterday = df[df[date_col_name] == pd.to_datetime(yesterday_date, format="%d/%m/%Y")].copy()
        
        if df_yesterday.empty:
            st.info(f"A lista não contem artistas Vybbe na data {yesterday_date}.")
        else:
            st.markdown(f"**Dados do dia: {yesterday_date}**")
            
            num_cols = len(df_yesterday)
            num_cols = min(num_cols, 5)
            cols = st.columns(num_cols)
            
            for i, (index, row) in enumerate(df_yesterday.iterrows()):
                with cols[i % num_cols]:
                    artist_name = row.get('Artista', '').split(',')[0].strip()
                    image_url = get_artist_image(artist_name)
                    if image_url:
                        st.image(image_url, width=150, caption=artist_name)
                    st.markdown(f"**Música:** {row.get('Música', 'N/A')}")
                    st.markdown(f"**Ranking:** {row.get('Rank', 'N/A')}")
                    st.markdown(f"**Dias no ranking:** {row.get('days_on_chart', 'N/A')}")
                    if 'Streams' in row:
                        st.markdown(f"**Streams:** {row.get('Streams', 'N/A')}")

        st.write("---")

        df['Mês'] = df[date_col_name].dt.strftime('%B')
        df['Ano'] = df[date_col_name].dt.year

        df_unique_items = df[item_col].unique()
        selected_item = st.selectbox(f"Selecione {item_type} para análise do ranking", df_unique_items, key=f"selectbox_{key_suffix}")
        
        df_filtered = df[df[item_col] == selected_item].copy()

        st.write("---")
        filter_option = st.radio("Filtro do Gráfico:", chart_filter_options, key=f"chart_filter_{key_suffix}")
        
        df_chart = df_filtered.copy()
        if filter_option == "Mês":
            df_chart = df_filtered[df_filtered['Mês'] == st.selectbox("Selecione o Mês:", df_filtered['Mês'].unique(), key=f"filter_month_{key_suffix}")]
        elif filter_option == "Ano":
            df_chart = df_filtered[df_filtered['Ano'] == st.selectbox("Selecione o Ano:", df_filtered['Ano'].unique(), key=f"filter_year_{key_suffix}")]
            
        y_axis_col = "Rank"
        y_axis_title = "Posição no Ranking"
        
        if "Songs" in section_title:
            chart_type = st.radio(
                "Tipo de visualização:", ("Ranking", "Streams"),
                key=f"radio_chart_type_{key_suffix}"
            )
            y_axis_col = "Rank" if chart_type == "Ranking" else "Streams"
            y_axis_title = "Posição no Ranking" if chart_type == "Ranking" else "Número de Streams"
            
            if y_axis_col == "Streams":
                df_chart['Streams'] = df_chart['Streams'].astype(str).str.replace('.', '').str.replace(',', '').astype(float)
        
        artist_name = None
        if item_type == 'o artista':
            artist_name = selected_item
        elif item_type == 'a música':
            artist_name_series = df[df['Música'] == selected_item]['Artista']
            if not artist_name_series.empty:
                artist_name = artist_name_series.iloc[0].split(',')[0].strip()
        
        image_url = get_artist_image(artist_name)
        
        if image_url:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="{image_url}" width="50" style="border-radius: 50%;">
                <h3>{y_axis_title} de '{selected_item}' ao Longo do Tempo</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.header(f"{y_axis_title} de '{selected_item}' ao Longo do Tempo")
            
        fig = px.line(
            df_chart, 
            x=date_col_name,
            y=y_axis_col,
            text=y_axis_col,
            line_shape='spline'
        )
        
        fig.update_traces(textposition='top center')
        fig.update_layout(
            xaxis_title="Dia",
            yaxis_title=y_axis_title,
            yaxis={'autorange': 'reversed'} if y_axis_col == 'Rank' else {}
        )
        st.plotly_chart(fig)
    
    st.write("---")
    
# --- aplicativo Streamlit ---

imagem = Image.open("logo_habbla_cor_positivo.png")
st.image(imagem,width=100)
st.title('🎶 Vybbe Dashboard Streams')

menu_principal = ["Daily Top Songs", "Daily Top Artists", "Daily Viral Songs"]
st.sidebar.title("Menu Principal")
with st.sidebar.expander("Spotify", expanded=True):
    opcao_selecionada = st.radio("Selecione uma opção:", menu_principal, key="main_menu_radio")

# Renderização do conteúdo principal com base na seleção do menu
if opcao_selecionada == "Daily Top Songs":
    st.header("Daily Top Songs")
    sub_opcao_songs = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs")
    if sub_opcao_songs == "Global":
        display_daily_chart(4, "Daily Top Songs Global", "a música", "songs_global", ["Geral", "Mês", "Ano"])
    elif sub_opcao_songs == "Brasil":
        display_daily_chart(5, "Daily Top Songs Brasil", "a música", "songs_brasil", ["Geral", "Mês", "Ano"])
elif opcao_selecionada == "Daily Top Artists":
    st.header("Daily Top Artists")
    sub_opcao_artists = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists")
    if sub_opcao_artists == "Global":
        display_daily_chart(0, "Daily Top Artists Global", "o artista", "artists_global", ["Geral", "Mês", "Ano"])
    elif sub_opcao_artists == "Brasil":
        display_daily_chart(1, "Daily Top Artists Brasil", "o artista", "artists_brasil", ["Mês", "Ano"])
elif opcao_selecionada == "Daily Viral Songs":
    st.header("Daily Viral Songs")
    sub_opcao_viral = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_viral")
    if sub_opcao_viral == "Global":
        display_daily_chart(8, "Daily Viral Songs Global", "a música", "viral_songs_global", ["Mês", "Ano"])
    elif sub_opcao_viral == "Brasil":
        display_daily_chart(9, "Daily Viral Songs Brasil", "a música", "viral_songs_brasil", ["Mês", "Ano"])