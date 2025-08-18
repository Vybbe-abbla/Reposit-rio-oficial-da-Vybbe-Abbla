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

st.set_page_config(page_title='Vybbe Charts', layout="wide")

# --- Configuração e Funções Globais (uma única vez) ---
load_dotenv()

# Pega o conteúdo da variável de ambiente como uma string
google_sheets_creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
planilha_completa = None # Inicializa com None por segurança

# Lógica de autenticação condensada e protegida
if not google_sheets_creds_json:
    st.error("A variável de ambiente GOOGLE_SHEETS_CREDENTIALS não foi encontrada.")
else:
    try:
        # Cria um arquivo JSON temporário a partir da string
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_creds_file:
            temp_creds_file.write(google_sheets_creds_json)
            temp_file_name = temp_creds_file.name

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(filename=temp_file_name, scopes=scopes)
        client = gspread.authorize(creds)
        planilha_completa = client.open(title="2025_Charts")
        os.remove(temp_file_name)
    except Exception as e:
        st.error(f"Erro ao autenticar com o Google Sheets: {e}")
        if 'temp_file_name' in locals() and os.path.exists(temp_file_name):
            os.remove(temp_file_name)

@st.cache_data
def load_data(sheet_index):
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

@st.cache_data
def get_album_image(album_name):
    if sp is None:
        return None
    try:
        # Busca o álbum na API do Spotify
        results = sp.search(q='album:' + album_name, type='album', limit=1)
        if results['albums']['items'] and results['albums']['items'][0]['images']:
            # Retorna a URL da imagem de maior resolução
            return results['albums']['items'][0]['images'][0]['url']
    except Exception as e:
        st.error(f"Erro ao buscar imagem do álbum {album_name}: {e}")
    return None

def display_chart(sheet_index, section_title, item_type, key_suffix, chart_type):
    st.subheader(section_title)
    df = load_data(sheet_index)

    if not df.empty:
        item_col = 'Música' if 'Música' in df.columns else ('Álbum' if 'Álbum' in df.columns else 'Artista')
        date_col_name = 'DATA' if 'DATA' in df.columns else 'Data'
        df[date_col_name] = pd.to_datetime(df[date_col_name], format="%d/%m/%Y")
        
        # Filtro de data específica para imagens
        latest_date = df[date_col_name].max()
        if latest_date is not pd.NaT:
            selected_date = st.date_input("Selecione a Data para Visualização", latest_date, key=f"date_input_{key_suffix}")
            df_display = df[df[date_col_name] == pd.to_datetime(selected_date)].copy()
        else:
            df_display = pd.DataFrame()
            st.info("Nenhum dado de data encontrado na planilha.")

        if not df_display.empty:
            st.markdown(f"**Dados do dia/semana:** {selected_date.strftime('%d/%m/%Y')}")
            num_cols = min(len(df_display), 5)
            cols = st.columns(num_cols)
            for i, (index, row) in enumerate(df_display.iterrows()):
                with cols[i % num_cols]:
                    # Lógica para obter a imagem correta (artista ou álbum)
                    image_url = None
                    if item_type == 'o álbum':
                        album_name = row.get('Álbum', '').split(',')[0].strip()
                        image_url = get_album_image(album_name)
                    else:
                        artist_name = row.get('Artista', '').split(',')[0].strip()
                        image_url = get_artist_image(artist_name)
                    
                    if image_url:
                        st.image(image_url, width=150, caption=row.get(item_col, 'N/A'))
                    
                    st.markdown(f"**Ranking:** {row.get('Rank', 'N/A')}")
                    st.markdown(f"**Dias no ranking:** {row.get('days_on_chart', 'N/A')}")
                    if 'Streams' in row:
                        st.markdown(f"**Streams:** {row.get('Streams', 'N/A')}")
                    
                    # Exibir a música/artista/álbum
                    if 'Música' in row:
                        st.markdown(f"**Música:** {row.get('Música', 'N/A')}")
                    elif 'Artista' in row:
                        st.markdown(f"**Artista:** {row.get('Artista', 'N/A')}")
                    elif 'Álbum' in row:
                        st.markdown(f"**Álbum:** {row.get('Álbum', 'N/A')}")
        else:
            st.info(f"Nenhum dado encontrado para a data selecionada: {selected_date.strftime('%d/%m/%Y')}.")

        st.write("---")

        df['Mês'] = df[date_col_name].dt.strftime('%B')
        df['Ano'] = df[date_col_name].dt.year
        df_unique_items = df[item_col].unique()
        selected_item = st.selectbox(f"Selecione {item_type} para análise do ranking", df_unique_items, key=f"selectbox_{key_suffix}")
        df_filtered = df[df[item_col] == selected_item].copy()
        
        st.write("---")
        # Remove a seleção de rádio e exibe apenas o filtro de período de datas
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data de Início", df_filtered[date_col_name].min(), key=f"start_date_{key_suffix}")
        with col2:
            end_date = st.date_input("Data de Fim", df_filtered[date_col_name].max(), key=f"end_date_{key_suffix}")
        df_chart = df_filtered[(df_filtered[date_col_name] >= pd.to_datetime(start_date)) & (df_filtered[date_col_name] <= pd.to_datetime(end_date))]

        y_axis_col = "Rank"
        y_axis_title = "Posição no Ranking"

        # Lógica para habilitar a opção de streams apenas para Daily Top Songs e Weekly Top Songs
        if "Top Songs" in section_title:
            chart_type_radio = st.radio(
                "Tipo de visualização:", ("Ranking", "Streams"),
                key=f"radio_chart_type_{key_suffix}"
            )
            y_axis_col = "Rank" if chart_type_radio == "Ranking" else "Streams"
            y_axis_title = "Posição no Ranking" if chart_type_radio == "Ranking" else "Número de Streams"
            
            if y_axis_col == "Streams" and 'Streams' in df_chart.columns:
                df_chart['Streams'] = df_chart['Streams'].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False).astype(float)
        
        image_url = None
        if item_type == 'o artista':
            artist_name = selected_item
            image_url = get_artist_image(artist_name)
        elif item_type == 'a música':
            artist_name_series = df[df['Música'] == selected_item]['Artista']
            if not artist_name_series.empty:
                artist_name = artist_name_series.iloc[0].split(',')[0].strip()
                image_url = get_artist_image(artist_name)
        elif item_type == 'o álbum':
            image_url = get_album_image(selected_item)
        
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

# --- Estrutura principal do aplicativo ---
st.title('🎶 Vybbe Dashboard Streams')

st.sidebar.title("Menu de Charts")
chart_selection = st.sidebar.radio("Selecione o tipo de chart:", ["Daily Charts", "Weekly Charts"])

if chart_selection == "Daily Charts":
    menu_daily = ["Daily Top Songs", "Daily Top Artists", "Daily Viral Songs"]
    with st.sidebar.expander("Spotify Daily", expanded=True):
        opcao_selecionada = st.radio("Selecione uma opção:", menu_daily, key="daily_menu_radio")
    
    if opcao_selecionada == "Daily Top Songs":
        st.header("Daily Top Songs")
        sub_opcao_songs = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs")
        if sub_opcao_songs == "Global":
            display_chart(4, "Daily Top Songs Global", "a música", "songs_global", 'daily')
        elif sub_opcao_songs == "Brasil":
            display_chart(5, "Daily Top Songs Brasil", "a música", "songs_brasil", 'daily')
    elif opcao_selecionada == "Daily Top Artists":
        st.header("Daily Top Artists")
        sub_opcao_artists = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists")
        if sub_opcao_artists == "Global":
            display_chart(0, "Daily Top Artists Global", "o artista", "artists_global", 'daily')
        elif sub_opcao_artists == "Brasil":
            display_chart(1, "Daily Top Artists Brasil", "o artista", "artists_brasil", 'daily')
    elif opcao_selecionada == "Daily Viral Songs":
        st.header("Daily Viral Songs")
        sub_opcao_viral = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_viral")
        if sub_opcao_viral == "Global":
            display_chart(8, "Daily Viral Songs Global", "a música", "viral_songs_global", 'daily')
        elif sub_opcao_viral == "Brasil":
            display_chart(9, "Daily Viral Songs Brasil", "a música", "viral_songs_brasil", 'daily')

elif chart_selection == "Weekly Charts":
    menu_weekly = ["Weekly Top Songs", "Weekly Top Artists", "Weekly Top Albums"]
    with st.sidebar.expander("Spotify Weekly", expanded=True):
        opcao_selecionada = st.radio("Selecione uma opção:", menu_weekly, key="weekly_menu_radio")

    if opcao_selecionada == "Weekly Top Songs":
        st.header("Weekly Top Songs")
        sub_opcao_songs_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs_weekly")
        if sub_opcao_songs_weekly == "Global":
            display_chart(6, "Weekly Top Songs Global", "a música", "weekly_songs_global", 'weekly')
        elif sub_opcao_songs_weekly == "Brasil":
            display_chart(7, "Weekly Top Songs Brasil", "a música", "weekly_songs_brasil", 'weekly')
    elif opcao_selecionada == "Weekly Top Artists":
        st.header("Weekly Top Artists")
        sub_opcao_artists_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists_weekly")
        if sub_opcao_artists_weekly == "Global":
            display_chart(2, "Weekly Top Artists Global", "o artista", "weekly_artists_global", 'weekly')
        elif sub_opcao_artists_weekly == "Brasil":
            display_chart(3, "Weekly Top Artists Brasil", "o artista", "weekly_artists_brasil", 'weekly')
    elif opcao_selecionada == "Weekly Top Albums":
        st.header("Weekly Top Albums")
        sub_opcao_albums_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_albums_weekly")
        if sub_opcao_albums_weekly == "Global":
            display_chart(10, "Weekly Top Albums Global", "o álbum", "weekly_albums_global", 'weekly')
        elif sub_opcao_albums_weekly == "Brasil":
            display_chart(11, "Weekly Top Albums Brasil", "o álbum", "weekly_albums_brasil", 'weekly')