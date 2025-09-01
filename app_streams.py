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

st.set_page_config(page_title='Vybbe Charts', layout="wide", initial_sidebar_state="expanded")

# --- Configuração e Funções Globais (uma única vez) ---
load_dotenv()

google_sheets_creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
planilha_completa = None

if not google_sheets_creds_json:
    st.error("A variável de ambiente GOOGLE_SHEETS_CREDENTIALS não foi encontrada.")
else:
    try:
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
        if 'temp_file_name' in locals() and os.path.exists(temp_creds_file):
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
        results = sp.search(q='album:' + album_name, type='album', limit=1)
        if results['albums']['items'] and results['albums']['items'][0]['images']:
            return results['albums']['items'][0]['images'][0]['url']
    except Exception as e:
        st.error(f"Erro ao buscar imagem do álbum {album_name}: {e}")
    return None
    
@st.cache_data
def get_track_album_image(track_name, artist_name):
    if sp is None:
        return None
    try:
        results = sp.search(q=f'track:{track_name} artist:{artist_name}', type='track', limit=1)
        if results['tracks']['items'] and results['tracks']['items'][0]['album']['images']:
            return results['tracks']['items'][0]['album']['images'][0]['url']
    except Exception as e:
        st.error(f"Erro ao buscar imagem do álbum para a música {track_name} de {artist_name}: {e}")
    return None

def format_br_number(number):
    try:
        # Converte para string e remove o decimal
        s = f"{int(number):,}"
        # Troca a vírgula por ponto para o padrão brasileiro
        return s.replace(",", ".")
    except (ValueError, TypeError):
        return str(number)

def display_chart(sheet_index, section_title, item_type, key_suffix, chart_type, platform):
    st.subheader(section_title)
    df = load_data(sheet_index)

    if df.empty:
        st.info(f"😪 Nenhum dado disponível para o chart de {section_title.replace('Global', 'Brasil').replace('Songs', 'Músicas').replace('Artists', 'Artistas').replace('Albums', 'Álbuns')}.")
        st.write("---")
        return

    item_col = 'Música' if 'Música' in df.columns else ('Álbum' if 'Álbum' in df.columns else ('Faixa' if 'Faixa' in df.columns else 'Artista'))
    date_col_name = 'DATA' if 'DATA' in df.columns else 'Data'
    
    if date_col_name not in df.columns:
        st.warning("Coluna de data não encontrada. Verifique se o nome da coluna é 'DATA' ou 'Data'.")
        st.write("---")
        return
        
    df[date_col_name] = pd.to_datetime(df[date_col_name], format="%d/%m/%Y")
    
    df_display = pd.DataFrame()
    selected_date_display = None
    
    if chart_type == 'daily':
        latest_date_available = df[date_col_name].max().date()
        yesterday = datetime.today().date() - timedelta(days=1)
        
        show_date_selector = st.checkbox("Pesquisar por datas anteriores?", key=f"checkbox_{key_suffix}")
        
        if show_date_selector:
            selected_date = st.date_input("Selecione a Data para Visualização", latest_date_available, key=f"date_input_{key_suffix}")
            df_display = df[df[date_col_name].dt.date == selected_date].copy()
            selected_date_display = selected_date
        else:
            df_display = df[df[date_col_name].dt.date == yesterday].copy()
            selected_date_display = yesterday

        if df_display.empty and not show_date_selector:
            st.info(f"😪 Nenhum dado encontrado para os artistas Vybbe no chart de {yesterday.strftime('%d/%m/%y')}.")
            
    elif chart_type == 'weekly':
        latest_date_available = df[date_col_name].max().date()
        
        show_date_selector = st.checkbox("Pesquisar por datas anteriores?", key=f"checkbox_{key_suffix}")

        if show_date_selector:
            selected_date = st.date_input("Selecione a Data para Visualização", latest_date_available, key=f"date_input_{key_suffix}")
            df_display = df[df[date_col_name].dt.date == selected_date].copy()
            selected_date_display = selected_date
        else:
            df_display = df[df[date_col_name].dt.date == latest_date_available].copy()
            selected_date_display = latest_date_available
        
        if not df_display.empty:
            st.markdown(f"**Semana Última Atualização:** {selected_date_display.strftime('%d/%m/%Y')}")
        else:
            if not show_date_selector:
                st.info(f"😪 Nenhum dado disponível para o chart de {section_title} na data {latest_date_available.strftime('%d/%m/%Y')}.")
            elif selected_date_display:
                st.info(f"Nenhum dado encontrado para a data selecionada: {selected_date_display.strftime('%d/%m/%Y')}.")
            
    if not df_display.empty:
        if chart_type == 'daily':
            corte_charts_value = df_display['Corte charts'].iloc[0] if 'Corte charts' in df_display.columns and not df_display.empty else "N/A"
            if selected_date_display:
                st.markdown(f"**Dados do dia:** {selected_date_display.strftime('%d/%m/%Y')}")
            if 'Daily Top Songs Brasil' in section_title and corte_charts_value != 'N/A':
                st.markdown(f"| **Corte do Chart:** {corte_charts_value}")
                
        num_cols = min(len(df_display), 5)
        cols = st.columns(num_cols)
        
        for i, (index, row) in enumerate(df_display.iterrows()):
            with cols[i % num_cols]:
                image_url = None
                
                if item_type == 'o artista':
                    artist_name = row.get('Artista', '').split(',')[0].strip()
                    image_url = get_artist_image(artist_name)
                elif item_type in ['a música', 'a faixa']:
                    track_name = row.get(item_col, '').split(',')[0].strip()
                    artist_name_col = 'Artista' if 'Artista' in df_display.columns else 'Criador'
                    artist_name = row.get(artist_name_col, '').split(',')[0].strip()
                    if "Songs" in section_title:
                        image_url = get_track_album_image(track_name, artist_name)
                        if not image_url:
                            image_url = get_artist_image(artist_name)
                    else:
                        image_url = get_artist_image(artist_name)
                elif item_type == 'o álbum':
                    album_name = row.get('Álbum', '').split(',')[0].strip()
                    image_url = get_album_image(album_name)

                if image_url:
                    st.image(image_url, width=150, caption=row.get(item_col, 'N/A'))
                else:
                    st.write(f"Imagem não encontrada para: {row.get(item_col, 'N/A')}")
                    
                st.markdown(f"**Ranking:** {row.get('Rank', 'N/A')}")
                st.markdown(f"**Rank anterior:** {row.get('previous_rank', 'N/A')}")
                
                if 'Viral' not in section_title:
                    if 'days_on_chart' in row and not pd.isna(row.get('days_on_chart')):
                        st.markdown(f"**Dias no ranking:** {row.get('days_on_chart', 'N/A')}")
                
                if platform == 'Spotify':
                    if 'Streams' in row and not pd.isna(row.get('Streams')):
                        if 'Viral' not in section_title:
                            st.markdown(f"**Streams:** {row.get('Streams', 'N/A')}")
                        
                if platform == 'Youtube':
                    if 'Videos' in section_title:
                        visualizacoes = row.get('Visualizações Diárias')
                        if visualizacoes and str(visualizacoes).replace('.', '').replace(',', '').isdigit():
                            try:
                                visualizacoes = int(str(visualizacoes).replace('.', '').replace(',', ''))
                                st.markdown(f"**Visualizações:** {format_br_number(visualizacoes)}")
                            except (ValueError, TypeError):
                                pass
                        st.markdown(f"**Dias no ranking:** {row.get('days_on_chart', 'N/A')}")
                    if 'Semanal' in section_title:
                        st.markdown(f"**Weekly on chart:** {row.get('Weeks_on_chart', 'N/A')}")
                        if 'Visualizações Semanais' in row and str(row.get('Visualizações Semanais', '0')).replace('.', '').replace(',', '').isdigit():
                            try:
                                visualizacoes = float(str(row.get('Visualizações Semanais', '0')).replace('.', '').replace(',', ''))
                                st.markdown(f"**Visualizações:** {format_br_number(visualizacoes)}")
                            except (ValueError, TypeError):
                                pass
                # Correção para o "Streams" do Weekly Top Songs Brasil
                if platform == 'Spotify' and 'Weekly Top Songs Brasil' in section_title:
                    if 'Streams' in row and not pd.isna(row.get('Streams')):
                        st.markdown(f"**Streams:** {row.get('Streams', 'N/A')}")
                        
        
        st.write("---")
    else:
        if selected_date_display:
            st.info(f"Nenhum dado encontrado para a data selecionada: {selected_date_display.strftime('%d/%m/%Y')}.")
        st.write("---")

    df['Mês'] = df[date_col_name].dt.strftime('%B')
    df['Ano'] = df[date_col_name].dt.year
    df_unique_items = sorted(df[item_col].unique())
    selected_item = st.selectbox(f"Selecione {item_type} para análise do ranking", df_unique_items, key=f"selectbox_{key_suffix}")
    df_filtered = df[df[item_col] == selected_item].copy()
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data de Início", df_filtered[date_col_name].min(), key=f"start_date_{key_suffix}")
    with col2:
        end_date = st.date_input("Data de Fim", df_filtered[date_col_name].max(), key=f"end_date_{key_suffix}")
    df_chart = df_filtered[(df_filtered[date_col_name] >= pd.to_datetime(start_date)) & (df_filtered[date_col_name] <= pd.to_datetime(end_date))]

    y_axis_col = "Rank"
    y_axis_title = "Posição no Ranking"
    y_tickformat = None

    if item_type in ["a música", "a faixa"]:
        chart_options = ["Ranking"]
        if "Streams" in df_chart.columns:
            chart_options.append("Streams")
        if "Visualizações Semanais" in df_chart.columns:
            chart_options.append("Visualizações")
            
        if len(chart_options) > 1:
            chart_type_radio = st.radio(
                "Tipo de visualização:", chart_options,
                key=f"radio_chart_type_{key_suffix}"
            )
            
            if chart_type_radio == "Ranking":
                y_axis_col = "Rank"
                y_axis_title = "Posição no Ranking"
            elif chart_type_radio == "Streams":
                y_axis_col = "Streams"
                y_axis_title = "Número de Streams"
            elif chart_type_radio == "Visualizações":
                y_axis_col = "Visualizações Semanais"
                y_axis_title = "Número de Visualizações"

    if y_axis_col in ["Streams", "Visualizações Semanais"] and y_axis_col in df_chart.columns:
        df_chart[y_axis_col] = df_chart[y_axis_col].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False).astype(float)
        df_chart['y_axis_formatted'] = df_chart[y_axis_col].apply(lambda x: format_br_number(x))
        y_tickformat = None
    
    text_col = 'y_axis_formatted' if 'y_axis_formatted' in df_chart.columns else y_axis_col

    image_url = None
    if item_type == 'o artista':
        image_url = get_artist_image(selected_item)
    elif item_type in ['a música', 'a faixa']:
        artist_name_series = df[df[item_col] == selected_item]['Artista']
        if not artist_name_series.empty:
            artist_name = artist_name_series.iloc[0].split(',')[0].strip()
            image_url = get_track_album_image(selected_item, artist_name)
            if not image_url:
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
        text=text_col,
        line_shape='spline'
    )
    
    fig.update_traces(textposition='top center')
    
    yaxis_config = {'title': y_axis_title}
    if y_axis_col == 'Rank':
        yaxis_config['autorange'] = 'reversed'
    if y_tickformat:
        yaxis_config['tickformat'] = y_tickformat
    
    fig.update_layout(
        xaxis_title="Dia",
        yaxis=yaxis_config
    )
    
    st.plotly_chart(fig)
    st.write("---")

def display_weekly_global_chart(global_sheet_index, global_section_title, global_item_type, global_key_suffix):
    st.subheader(global_section_title)
    df = load_data(global_sheet_index)

    if df.empty:
        st.info(f"😪 Nenhum dado disponível para o chart de {global_section_title}.")
        st.write("---")
        return

    date_col_name = 'Data' if 'Data' in df.columns else 'DATA'
    df[date_col_name] = pd.to_datetime(df[date_col_name], format="%d/%m/%Y")
    
    latest_date_available = df[date_col_name].max().date()
    yesterday = datetime.today().date() - timedelta(days=1)
    
    show_date_selector = st.checkbox("Pesquisar por datas anteriores?", key=f"checkbox_{global_key_suffix}")
    
    df_display = pd.DataFrame()
    selected_date_display = None
    
    if show_date_selector:
        selected_date = st.date_input("Selecione a Data para Visualização", latest_date_available, key=f"date_input_{global_key_suffix}")
        df_display = df[df[date_col_name].dt.date == selected_date].copy()
        selected_date_display = selected_date
    else:
        df_display = df[df[date_col_name].dt.date == yesterday].copy()
        selected_date_display = yesterday

    if not df_display.empty:
        st.markdown(f"**Dados do dia:** {selected_date_display.strftime('%d/%m/%Y')}")
    else:
        if not show_date_selector:
            st.info(f"😪 Nenhum dado encontrado para os artistas Vybbe no chart de {yesterday.strftime('%d/%m/%Y')}.")
        elif selected_date_display:
            st.info(f"Nenhum dado encontrado para a data selecionada: {selected_date_display.strftime('%d/%m/%Y')}.")
        st.write("---")
        return

    item_col = 'Música' if 'Música' in df.columns else ('Álbum' if 'Álbum' in df.columns else 'Artista')
    num_cols = min(len(df_display), 5)
    cols = st.columns(num_cols)
    
    for i, (index, row) in enumerate(df_display.iterrows()):
        with cols[i % num_cols]:
            image_url = None
            
            if global_item_type == 'o artista':
                image_url = get_artist_image(row.get('Artista', '').split(',')[0].strip())
            elif global_item_type in ['a música', 'a faixa']:
                track_name = row.get(item_col, '').split(',')[0].strip()
                artist_name = row.get('Artista', '').split(',')[0].strip()
                image_url = get_track_album_image(track_name, artist_name)
                if not image_url:
                    image_url = get_artist_image(artist_name)
            elif global_item_type == 'o álbum':
                image_url = get_album_image(row.get('Álbum', '').split(',')[0].strip())

            if image_url:
                st.image(image_url, width=150, caption=row.get(item_col, 'N/A'))
            else:
                st.write(f"Imagem não encontrada para: {row.get(item_col, 'N/A')}")
                
            st.markdown(f"**Ranking:** {row.get('Rank', 'N/A')}")
            st.markdown(f"**Rank anterior:** {row.get('previous_rank', 'N/A')}")
            
    st.write("---")

    df_unique_items = sorted(df[item_col].unique())
    selected_item = st.selectbox(f"Selecione {global_item_type} para análise do ranking", df_unique_items, key=f"selectbox_{global_key_suffix}")
    df_filtered = df[df[item_col] == selected_item].copy()
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data de Início", df_filtered[date_col_name].min(), key=f"start_date_{global_key_suffix}")
    with col2:
        end_date = st.date_input("Data de Fim", df_filtered[date_col_name].max(), key=f"end_date_{global_key_suffix}")
    df_chart = df_filtered[(df_filtered[date_col_name] >= pd.to_datetime(start_date)) & (df_filtered[date_col_name] <= pd.to_datetime(end_date))]

    y_axis_col = "Rank"
    y_axis_title = "Posição no Ranking"
    
    image_url = None
    if global_item_type == 'o artista':
        image_url = get_artist_image(selected_item)
    elif global_item_type in ['a música', 'a faixa']:
        artist_name_series = df[df[item_col] == selected_item]['Artista']
        if not artist_name_series.empty:
            artist_name = artist_name_series.iloc[0].split(',')[0].strip()
            image_url = get_track_album_image(selected_item, artist_name)
            if not image_url:
                image_url = get_artist_image(artist_name)
    elif global_item_type == 'o álbum':
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
    
    yaxis_config = {'title': y_axis_title}
    if y_axis_col == 'Rank':
        yaxis_config['autorange'] = 'reversed'
    
    fig.update_layout(
        xaxis_title="Dia",
        yaxis=yaxis_config
    )
    
    st.plotly_chart(fig)
    st.write("---")


# --- Estrutura principal do aplicativo ---
st.title('🎶 Vybbe Dashboard Streaming')
st.markdown("Bem-vindo(a) ao seu portal de inteligência de mercado musical. Explore as tendências e rankings das principais plataformas de streaming, com dados atualizados e análises detalhadas para auxiliar na sua estratégia artística.")
st.write("---")

st.sidebar.title("Menu de Plataformas")
plataforma_selecionada = st.sidebar.radio(
    "Selecione a Plataforma:", 
    ["Spotify", "Youtube", "Deezer", "Amazon", "Apple Music"]
)

if plataforma_selecionada == "Spotify":
    menu_spotify = ["Daily Charts", "Weekly Charts"]
    spotify_charts_selection = st.sidebar.radio("Selecione o tipo de chart:", menu_spotify)
    
    if spotify_charts_selection == "Daily Charts":
        with st.sidebar.expander("Spotify Daily", expanded=True):
            opcao_selecionada = st.radio("Selecione uma opção:", ["Daily Top Songs", "Daily Top Artists", "Daily Viral Songs"], key="daily_menu_radio")
        
        if opcao_selecionada == "Daily Top Songs":
            st.header("Daily Top Songs")
            sub_opcao_songs = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs")
            if sub_opcao_songs == "Global":
                display_chart(4, "Daily Top Songs Global", "a música", "songs_global", 'daily', 'Spotify')
            elif sub_opcao_songs == "Brasil":
                display_chart(5, "Daily Top Songs Brasil", "a música", "songs_brasil", 'daily', 'Spotify')
        elif opcao_selecionada == "Daily Top Artists":
            st.header("Daily Top Artists")
            sub_opcao_artists = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists")
            if sub_opcao_artists == "Global":
                display_chart(0, "Daily Top Artists Global", "o artista", "artists_global", 'daily', 'Spotify')
            elif sub_opcao_artists == "Brasil":
                display_chart(1, "Daily Top Artists Brasil", "o artista", "artists_brasil", 'daily', 'Spotify')
        elif opcao_selecionada == "Daily Viral Songs":
            st.header("Daily Viral Songs")
            sub_opcao_viral = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_viral")
            if sub_opcao_viral == "Global":
                display_chart(8, "Daily Viral Songs Global", "a música", "viral_songs_global", 'daily', 'Spotify')
            elif sub_opcao_viral == "Brasil":
                display_chart(9, "Daily Viral Songs Brasil", "a música", "viral_songs_brasil", 'daily', 'Spotify')

    elif spotify_charts_selection == "Weekly Charts":
        with st.sidebar.expander("Spotify Weekly", expanded=True):
            opcao_selecionada = st.radio("Selecione uma opção:", ["Weekly Top Songs", "Weekly Top Artists", "Weekly Top Albums"], key="weekly_menu_radio")

        if opcao_selecionada == "Weekly Top Songs":
            st.header("Weekly Top Songs")
            sub_opcao_songs_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs_weekly")
            if sub_opcao_songs_weekly == "Global":
                display_weekly_global_chart(6, "Weekly Top Songs Global", "a música", "weekly_songs_global")
            elif sub_opcao_songs_weekly == "Brasil":
                display_chart(7, "Weekly Top Songs Brasil", "a música", "weekly_songs_brasil", 'weekly', 'Spotify')
        elif opcao_selecionada == "Weekly Top Artists":
            st.header("Weekly Top Artists")
            sub_opcao_artists_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists_weekly")
            if sub_opcao_artists_weekly == "Global":
                display_weekly_global_chart(2, "Weekly Top Artists Global", "o artista", "weekly_artists_global")
            elif sub_opcao_artists_weekly == "Brasil":
                display_chart(3, "Weekly Top Artists Brasil", "o artista", "weekly_artists_brasil", 'weekly', 'Spotify')
        elif opcao_selecionada == "Weekly Top Albums":
            st.header("Weekly Top Albums")
            sub_opcao_albums_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_albums_weekly")
            if sub_opcao_albums_weekly == "Global":
                display_weekly_global_chart(10, "Weekly Top Albums Global", "o álbum", "weekly_albums_global")
            elif sub_opcao_albums_weekly == "Brasil":
                display_chart(11, "Weekly Top Albums Brasil", "o álbum", "weekly_albums_brasil", 'weekly', 'Spotify')

elif plataforma_selecionada == "Youtube":
    with st.sidebar.expander("YouTube Charts", expanded=True):
        opcao_selecionada_youtube = st.radio("Selecione uma opção:", ["Top Videos Diários", "Top Shorts Diários", "Top Clipes Semanal", "Top Faixas Semanal", "Top Artistas Semanal"], key="youtube_menu_radio")
    
    if opcao_selecionada_youtube == "Top Videos Diários":
        sheet_index = 18
        display_chart(sheet_index, "Top Videos Diários Brasil", "a música", "videos_diarios_br", 'daily', 'Youtube')

    elif opcao_selecionada_youtube == "Top Shorts Diários":
        sheet_index = 19
        display_chart(sheet_index, "Músicas mais tocadas nos Shorts neste dia", "a música", "shorts_diarios_br", 'daily', 'Youtube')

    elif opcao_selecionada_youtube == "Top Clipes Semanal":
        sheet_index = 17
        display_chart(sheet_index, "Top Clipes Semanal Brasil", "a música", "clipes_semanal_br", 'weekly', 'Youtube')

    elif opcao_selecionada_youtube == "Top Faixas Semanal":
        sheet_index = 16
        display_chart(sheet_index, "Top Faixas Semanal Brasil", "a faixa", "faixas_semanal_br", 'weekly', 'Youtube')

    elif opcao_selecionada_youtube == "Top Artistas Semanal":
        sheet_index = 15
        display_chart(sheet_index, "Top Artistas Semanal Brasil", "o artista", "artistas_semanal_br", 'weekly', 'Youtube')

elif plataforma_selecionada == "Deezer":
    st.header("Daily Top Songs Deezer")
    display_chart(sheet_index=12, section_title="Daily Top Songs Deezer", item_type="a música", key_suffix="songs_deezer", chart_type='daily', platform='Deezer')

elif plataforma_selecionada == "Amazon":
    st.header("Daily Top Songs Amazon")
    display_chart(sheet_index=13, section_title="Daily Top Songs Amazon", item_type="a música", key_suffix="songs_amazon", chart_type='daily', platform='Amazon')

elif plataforma_selecionada == "Apple Music":
    st.header("Daily Top Songs Apple Music")
    display_chart(sheet_index=14, section_title="Daily Top Songs Apple Music", item_type="a música", key_suffix="songs_apple", chart_type='daily', platform='Apple Music')

st.write("---")
st.markdown("Desenvolvido com Python e Streamlit, este painel é uma ferramenta essencial para a análise de mercado musical. Os dados aqui apresentados refletem as tendências mais recentes, permitindo uma tomada de decisão estratégica e ágil para artistas e profissionais da indústria.")