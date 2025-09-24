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

st.set_page_config(page_title='Vybbe Charts', layout="wide", initial_sidebar_state="expanded")

load_dotenv()

google_sheets_creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
planilha_completa = None

if not google_sheets_creds_json:
    st.error("A variável de ambiente GOOGLE_SHEETS_CREDENTIALS não foi encontrada.")
else:
    temp_file_name = None
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
        temp_file_name = None # Limpa a referência após remoção
    except Exception as e:
        st.error(f"Erro ao autenticar com o Google Sheets: {e}")
    finally:
        if temp_file_name and os.path.exists(temp_file_name):
            os.remove(temp_file_name)

@st.cache_data
def load_data(sheet_index):
    if not planilha_completa:
        return pd.DataFrame()

    try:
        worksheet = planilha_completa.get_worksheet(sheet_index)
        if sheet_index == 5:
            expected_headers = ['DATA', 'Rank', 'uri', 'Artista', 'Música', 'source', 'peak_rank', 'previous_rank', 'days_on_chart', 'Corte charts', 'Data de Pico', 'Streams']
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
        if isinstance(number, (int, float)):
            # Formata como inteiro, adiciona separador de milhares (virgula),
            # e substitui para o padrão BR (ponto como milhar, vírgula como decimal)
            s = f"{int(number):,}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return str(number)
    except (ValueError, TypeError):
        return str(number)
        
def format_br_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        return date_obj.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return str(date_str)

def display_chart(sheet_index, section_title, item_type, key_suffix, chart_type, platform):
    st.header(section_title)
    df = load_data(sheet_index)

    if df.empty:
        st.info(f"😪 Nenhum dado disponível para o chart de {section_title.replace('Global', 'Brasil').replace('Songs', 'Músicas').replace('Artists', 'Artistas').replace('Albums', 'Álbums')}.")
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
        total_artistas = df_display['Artista'].nunique()
        if item_type == 'o artista':
            col_artists = st.columns(1)
            with col_artists[0]:
                st.metric(label="Total de Artistas", value=total_artistas)
        else:
            total_items = df_display[item_col].nunique() if item_col in df_display.columns else 0
            col_artists, col_tracks = st.columns(2)
            with col_artists:
                st.metric(label="Total de Artistas", value=total_artistas)
            with col_tracks:
                st.metric(label=f"Total de {item_col}s", value=total_items)
        
        st.write("---")

        # --- CORREÇÃO DE EXIBIÇÃO DE DATA (PARA ATENDER À SUA PRIMEIRA SOLICITAÇÃO) ---
        if 'Daily Top Songs' in section_title:
            if selected_date_display:
                st.markdown(f"**Dados do dia:** {selected_date_display.strftime('%d/%m/%Y')}") 
            corte_charts_value = df_display['Corte charts'].iloc[0] if 'Corte charts' in df_display.columns and not df_display.empty else "N/A"
            if 'Daily Top Songs Brasil' in section_title and corte_charts_value != 'N/A':
                st.markdown(f"**Corte do Chart:** {corte_charts_value}")
        else:
            if selected_date_display:
                st.markdown(f"**Dados do dia:** {selected_date_display.strftime('%d/%m/%Y')}")

        # --- CÓDIGO DE VISUALIZAÇÃO ---
        has_streams = platform == 'Spotify' and 'Streams' in df_display.columns and not df_display['Streams'].isna().all() and "Artists" not in section_title and "Albums" not in section_title
        
        has_peak_date = 'Data de Pico' in df_display.columns or 'Data do Pico' in df_display.columns
        
        has_views_youtube = platform == 'Youtube' and 'Visualizações Semanais' in df_display.columns and not df_display['Visualizações Semanais'].isna().all()

        column_ratios = [0.5, 3.5, 0.7, 0.7, 0.9]
        if has_streams:
            column_ratios.append(1.5)
        if has_views_youtube:
            column_ratios.append(1.5)
        if has_peak_date:
            column_ratios.append(1.2)
        
        header_cols = st.columns(column_ratios)
        
        with header_cols[0]:
            st.markdown("<b>#</b>", unsafe_allow_html=True)
        with header_cols[1]:
            header_text = "ARTIST" if "Top Artists" in section_title or "Top Artistas" in section_title else ("ALBUM" if "Top Albums" in section_title else "TRACK")
            st.markdown(f"<b>{header_text}</b>", unsafe_allow_html=True)
        with header_cols[2]:
            st.markdown("<b>Peak</b>", unsafe_allow_html=True)
        with header_cols[3]:
            st.markdown("<b>Prev</b>", unsafe_allow_html=True)
        with header_cols[4]:
            st.markdown("<b>Streak</b>", unsafe_allow_html=True)

        col_index = 5
        if has_streams:
            with header_cols[col_index]:
                st.markdown("<b>Streams</b>", unsafe_allow_html=True)
            col_index += 1
        
        if has_views_youtube:
            with header_cols[col_index]:
                st.markdown("<b>Visualizações</b>", unsafe_allow_html=True)
            col_index += 1
        
        if has_peak_date:
            with header_cols[col_index]:
                st.markdown("<b>Peak Date</b>", unsafe_allow_html=True)

        st.markdown("---")

        for index, row in df_display.iterrows():
            rank = row.get('Rank', 'N/A')
            item_name = row.get(item_col, '').strip()
            artist_name_col = 'Artista' if 'Artista' in df_display.columns else 'Criador'
            artist_name = row.get(artist_name_col, 'N/A').strip()
            
            peak_rank = row.get('peak_rank', 'N/A')
            previous_rank = row.get('previous_rank', 'N/A')
            
            streak = "N/A"
            if "Viral" in section_title or chart_type == 'daily':
                streak = row.get('days_on_chart', 'N/A')
            elif ("Top Faixas Semanal" in section_title):
                if platform == 'Youtube':
                    streak = row.get('days_on_chart', 'N/A')
            elif ("Weekly Top Songs Brasil" in section_title or "Weekly Top Artists Brasil" in section_title):
                streak = row.get('weeks_on_chart', 'N/A')
            elif ("Top Artistas Semanal" in section_title):
                if platform == 'Youtube':
                    streak = row.get('Weeks_on_chart', 'N/A')
            elif "Weekly Top Albums Brasil" in section_title:
                streak = row.get('weeks_on_chart', 'N/A')
            else:
                streak = row.get('days_on_chart', 'N/A')
            
            if "Top Artists" in section_title or "Top Albums" in section_title:
                streams = "N/A"
            else:
                streams = 'N/A'
                if platform == 'Spotify':
                    streams = row.get('Streams', 'N/A')
                elif platform == 'Youtube':
                    streams = row.get('Visualizações Diárias', 'N/A')
                    if 'Semanal' in section_title:
                        streams = row.get('Visualizações Semanais', 'N/A')
            
            peak_date = row.get('Data de Pico') or row.get('Data do Pico', 'N/A')
            if peak_date != 'N/A':
                peak_date = format_br_date(peak_date)

            image_url = None
            
            if platform == 'Youtube':
                artist_for_image = artist_name.split(',')[0].strip() if isinstance(artist_name, str) else artist_name
                image_url = get_artist_image(artist_for_image)
            elif item_type in ['a música', 'a faixa']:
                image_url = get_track_album_image(item_name, artist_name)
            elif item_type == 'o artista':
                image_url = get_artist_image(artist_name.split(',')[0].strip())
            elif item_type == 'o álbum':
                image_url = get_album_image(item_name)
            
            cols = st.columns(column_ratios)

            with cols[0]:
                st.markdown(f"<p style='font-size:20px; font-weight:bold;'>{rank}</p>", unsafe_allow_html=True)
            
            with cols[1]:
                track_cols = st.columns([0.7, 3])
                with track_cols[0]:
                    if image_url:
                        # 🎯 CORREÇÃO: Tamanho da imagem padronizado para 200
                        st.image(image_url, width=200, caption="")
                    else:
                        st.write("🖼️")
                with track_cols[1]:
                    st.markdown(f"**{item_name}**")
                    if item_type != 'o artista':
                        st.markdown(f"<span style='color: gray; font-size: 16px;'>{artist_name}</span>", unsafe_allow_html=True)
            
            with cols[2]:
                st.markdown(f"<span style='font-size: 16px;'>{peak_rank}</span>", unsafe_allow_html=True)
                
            with cols[3]:
                st.markdown(f"<span style='font-size: 16px;'>{previous_rank}</span>", unsafe_allow_html=True)

            with cols[4]:
                st.markdown(f"<span style='font-size: 16px;'>{streak}</span>", unsafe_allow_html=True)
            
            col_index = 5
            if has_streams:
                with cols[col_index]:
                    st.markdown(f"<span style='font-size: 16px;'>{streams}</span>", unsafe_allow_html=True)
                col_index += 1
            
            if has_views_youtube:
                with cols[col_index]:
                    views = row.get('Visualizações Semanais', 'N/A')
                    if views != 'N/A' and str(views).replace('.', '').replace(',', '').isdigit():
                        st.markdown(f"<span style='font-size: 16px;'>{format_br_number(views)}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='font-size: 16px;'>{views}</span>", unsafe_allow_html=True)
                col_index += 1

            if has_peak_date:
                with cols[col_index]:
                    st.markdown(f"<span style='font-size: 16px;'>{peak_date}</span>", unsafe_allow_html=True)
            
            st.markdown("---")
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
        # Garante que st.date_input use um objeto datetime.date
        min_date = df_filtered[date_col_name].min().date() if not df_filtered.empty else datetime.today().date()
        start_date = st.date_input("Data de Início", min_date, key=f"start_date_{key_suffix}")
    with col2:
        # Garante que st.date_input use um objeto datetime.date
        max_date = df_filtered[date_col_name].max().date() if not df_filtered.empty else datetime.today().date()
        end_date = st.date_input("Data de Fim", max_date, key=f"end_date_{key_suffix}")
    
    # --- CORREÇÃO DE FILTRAGEM DE DATA APLICADA AQUI ---
    # Usa .dt.date na coluna do DataFrame para comparar objetos datetime.date (start_date/end_date)
    # com a parte da data da coluna do DataFrame (evitando problemas de timestamp).
    df_chart = df_filtered[
        (df_filtered[date_col_name].dt.date >= start_date) & 
        (df_filtered[date_col_name].dt.date <= end_date)
    ].copy()
    # FIM DA CORREÇÃO

    y_axis_col = "Rank"
    y_axis_title = "Posição no Ranking"
    y_tickformat = None

    if item_type in ["a música", "a faixa"]:
        chart_options = ["Ranking"]
        if "Streams" in df_chart.columns and not df_chart['Streams'].isna().all():
            chart_options.append("Streams")
        if "Visualizações Semanais" in df_chart.columns and not df_chart['Visualizações Semanais'].isna().all():
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
        # Conversão mais segura de streams/visualizações para float antes de formatar
        df_chart[y_axis_col] = df_chart[y_axis_col].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False).astype(float)
        df_chart['y_axis_formatted'] = df_chart[y_axis_col].apply(lambda x: format_br_number(x))
        y_tickformat = None
    
    text_col = 'y_axis_formatted' if 'y_axis_formatted' in df_chart.columns else y_axis_col

    image_url = None
    artist_name = ''
    if item_type == 'o artista':
        artist_name = selected_item
    elif item_type in ['a música', 'a faixa']:
        artist_name_series = df[df[item_col] == selected_item]['Artista']
        if not artist_name_series.empty:
            artist_name = artist_name_series.iloc[0].split(',')[0].strip()
    
    if platform == 'Youtube':
        artist_for_image = artist_name.split(',')[0].strip() if isinstance(artist_name, str) else artist_name
        image_url = get_artist_image(artist_for_image)
    elif item_type == 'o artista':
        image_url = get_artist_image(selected_item)
    elif item_type in ['a música', 'a faixa']:
        if artist_name:
            image_url = get_track_album_image(selected_item, artist_name)
            if not image_url:
                image_url = get_artist_image(artist_name)
    elif item_type == 'o álbum':
        image_url = get_album_image(selected_item)
    
    if image_url:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="{image_url}" width=60 style="border-radius: 50%;">
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
    st.header(global_section_title)
    df = load_data(global_sheet_index)

    if df.empty:
        st.info(f"😪 Nenhum dado disponível para o chart de {global_section_title}.")
        st.write("---")
        return
    
    item_col = 'Música' if 'Música' in df.columns else ('Álbum' if 'Álbum' in df.columns else ('Faixa' if 'Faixa' in df.columns else 'Artista'))

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
        df_display = df[df[date_col_name].dt.date == latest_date_available].copy()
        selected_date_display = latest_date_available

    if not df_display.empty:
        st.markdown(f"**Dados do dia:** {selected_date_display.strftime('%d/%m/%Y')}")
    else:
        if not show_date_selector:
            st.info(f"😪 Nenhum dado encontrado para os artistas Vybbe no chart de {yesterday.strftime('%d/%m/%Y')}.")
        elif selected_date_display:
            st.info(f"Nenhum dado encontrado para a data selecionada: {selected_date_display.strftime('%d/%m/%Y')}.")
        st.write("---")
        return

    total_artistas = df_display['Artista'].nunique()
    if global_item_type == 'o artista':
        col_artists = st.columns(1)
        with col_artists[0]:
            st.metric(label="Total de Artistas", value=total_artistas)
    else:
        total_items = df_display[item_col].nunique() if item_col in df_display.columns else 0
        col_artists, col_tracks = st.columns(2)
        with col_artists:
            st.metric(label="Total de Artistas", value=total_artistas)
        with col_tracks:
            st.metric(label=f"Total de {item_col}s", value=total_items)
            
    st.write("---")
    
    # --- NOVO CÓDIGO DE VISUALIZAÇÃO (GLOBAL) ---
    has_streams = 'Streams' in df_display.columns and not df_display['Streams'].isna().all() and "Artists" not in global_section_title and "Albums" not in global_section_title
    
    has_peak_date = 'Data de Pico' in df_display.columns or 'Data do Pico' in df_display.columns
    
    has_views_youtube = 'Visualizações Semanais' in df_display.columns and not df_display['Visualizações Semanais'].isna().all()
    
    column_ratios = [0.5, 3.5, 0.7, 0.7, 0.9]
    if has_streams:
        column_ratios.append(1.5)
    if has_views_youtube:
        column_ratios.append(1.5)
    if has_peak_date:
        column_ratios.append(1.2)
    
    header_cols = st.columns(column_ratios)

    with header_cols[0]:
        st.markdown("<b>#</b>", unsafe_allow_html=True)
    with header_cols[1]:
        header_text = "ARTIST" if "Top Artists" in global_section_title else ("ALBUM" if "Top Albums" in global_section_title else "TRACK")
        st.markdown(f"<b>{header_text}</b>", unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown("<b>Peak</b>", unsafe_allow_html=True)
    with header_cols[3]:
        st.markdown("<b>Prev</b>", unsafe_allow_html=True)
    with header_cols[4]:
        st.markdown("<b>Streak</b>", unsafe_allow_html=True)

    col_index = 5
    if has_streams:
        with header_cols[col_index]:
            st.markdown("<b>Streams</b>", unsafe_allow_html=True)
        col_index += 1
    
    if has_views_youtube:
        with header_cols[col_index]:
            st.markdown("<b>Visualizações</b>", unsafe_allow_html=True)
        col_index += 1
    
    if has_peak_date:
        with header_cols[col_index]:
            st.markdown("<b>Peak Date</b>", unsafe_allow_html=True)

    st.markdown("---")
    
    for index, row in df_display.iterrows():
        rank = row.get('Rank', 'N/A')
        item_name = row.get(item_col, '').strip()
        artist_name_col = 'Artista' if 'Artista' in df_display.columns else 'Criador'
        artist_name = row.get(artist_name_col, 'N/A').strip()
        peak_rank = row.get('peak_rank', 'N/A')
        previous_rank = row.get('previous_rank', 'N/A')
        
        streak = "N/A"
        if "Weekly Top Artists Global" in global_section_title or "Weekly Top Albums Global" in global_section_title or "Weekly Top Songs Global" in global_section_title:
            streak = row.get('weeks_on_chart', 'N/A')
        else:
            streak = row.get('days_on_chart', 'N/A')

        if "Top Artists" in global_section_title or "Top Albums" in global_section_title:
            streams = "N/A"
        else:
            streams = row.get('Streams', 'N/A')
        
        peak_date = row.get('Data de Pico') or row.get('Data do Pico', 'N/A')
        if peak_date != 'N/A':
            peak_date = format_br_date(peak_date)
        
        image_url = None
        
        if global_item_type in ['a música', 'a faixa']:
            image_url = get_track_album_image(item_name, artist_name)
        elif global_item_type == 'o artista':
            image_url = get_artist_image(artist_name.split(',')[0].strip())
        elif global_item_type == 'o álbum':
            image_url = get_album_image(item_name)

        cols = st.columns(column_ratios)
        with cols[0]:
            st.markdown(f"<p style='font-size:20px; font-weight:bold;'>{rank}</p>", unsafe_allow_html=True)
        with cols[1]:
            track_cols = st.columns([0.7, 3])
            with track_cols[0]:
                if image_url:
                    # 🎯 CORREÇÃO: Tamanho da imagem padronizado para 200
                    st.image(image_url, width=200, caption="")
                else:
                    st.write("🖼️")
            with track_cols[1]:
                st.markdown(f"**{item_name}**")
                if global_item_type != 'o artista':
                    st.markdown(f"<span style='color: gray; font-size: 16px;'>{artist_name}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<span style='font-size: 16px;'>{peak_rank}</span>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<span style='font-size: 16px;'>{previous_rank}</span>", unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"<span style='font-size: 16px;'>{streak}</span>", unsafe_allow_html=True)
        
        col_index = 5
        if has_streams:
            with cols[col_index]:
                if streams != 'N/A' and str(streams).replace('.', '').replace(',', '').isdigit():
                    st.markdown(f"<span style='font-size: 16px;'>{format_br_number(streams)}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='font-size: 16px;'>N/A</span>", unsafe_allow_html=True)
            col_index += 1

        if has_views_youtube:
            with cols[col_index]:
                views = row.get('Visualizações Semanais', 'N/A')
                if views != 'N/A' and str(views).replace('.', '').replace(',', '').isdigit():
                    st.markdown(f"<span style='font-size: 16px;'>{format_br_number(views)}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='font-size: 16px;'>{views}</span>", unsafe_allow_html=True)
            col_index += 1
        
        if has_peak_date:
            with cols[col_index]:
                st.markdown(f"<span style='font-size: 16px;'>{peak_date}</span>", unsafe_allow_html=True)
        
        st.markdown("---")

    df_unique_items = sorted(df[item_col].unique())
    selected_item = st.selectbox(f"Selecione {global_item_type} para análise do ranking", df_unique_items, key=f"selectbox_{global_key_suffix}")
    df_filtered = df[df[item_col] == selected_item].copy()
    
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        min_date = df_filtered[date_col_name].min().date() if not df_filtered.empty else datetime.today().date()
        start_date = st.date_input("Data de Início", min_date, key=f"start_date_{global_key_suffix}")
    with col2:
        max_date = df_filtered[date_col_name].max().date() if not df_filtered.empty else datetime.today().date()
        end_date = st.date_input("Data de Fim", max_date, key=f"end_date_{global_key_suffix}")
        
    # --- CORREÇÃO DE FILTRAGEM DE DATA APLICADA AQUI (Global Weekly) ---
    df_chart = df_filtered[
        (df_filtered[date_col_name].dt.date >= start_date) & 
        (df_filtered[date_col_name].dt.date <= end_date)
    ].copy()
    # FIM DA CORREÇÃO

    y_axis_col = "Rank"
    y_axis_title = "Posição no Ranking"
    
    image_url = None
    artist_name = ''
    if global_item_type == 'o artista':
        artist_name = selected_item
    elif global_item_type in ['a música', 'a faixa']:
        artist_name_series = df[df[item_col] == selected_item]['Artista']
        if not artist_name_series.empty:
            artist_name = artist_name_series.iloc[0].split(',')[0].strip()
    
    if global_item_type == 'o artista':
        image_url = get_artist_image(selected_item)
    elif global_item_type in ['a música', 'a faixa']:
        if artist_name:
            image_url = get_track_album_image(selected_item, artist_name)
            if not image_url:
                image_url = get_artist_image(artist_name)
    elif global_item_type == 'o álbum':
        image_url = get_album_image(selected_item)
    
    if image_url:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="{image_url}" width=60 style="border-radius: 50%;">
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

try:
    imagem_logo = Image.open('logo_Charts.jpg')
    st.image(imagem_logo)
except FileNotFoundError:
    st.header("Logo 'habbla.jpg' não encontrada.")
st.write("")

import streamlit as st
st.markdown(
    '<a href="https://vybbe-habbla-analytics-spotify.streamlit.app/" target="_blank">Clique aqui para ir para a Análise Popularidade Spotify</a>',
    unsafe_allow_html=True
)

st.title('🎶 Vybbe Dashboard Streaming')
st.markdown("Bem-vindo(a) ao seu portal de inteligência de mercado musical. Explore as tendências e rankings das principais plataformas de streaming, com dados atualizados e análises detalhadas para auxiliar na sua estratégia artística.")
st.write("---")

st.sidebar.title("Menu Plataformas")
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
            sub_opcao_songs = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs")
            if sub_opcao_songs == "Global":
                display_chart(4, "Daily Top Songs Global", "a música", "songs_global", 'daily', 'Spotify')
            elif sub_opcao_songs == "Brasil":
                display_chart(5, "Daily Top Songs Brasil", "a música", "songs_brasil", 'daily', 'Spotify')
        elif opcao_selecionada == "Daily Top Artists":
            sub_opcao_artists = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists")
            if sub_opcao_artists == "Global":
                display_chart(0, "Daily Top Artists Global", "o artista", "artists_global", 'daily', 'Spotify')
            elif sub_opcao_artists == "Brasil":
                display_chart(1, "Daily Top Artists Brasil", "o artista", "artists_brasil", 'daily', 'Spotify')
        elif opcao_selecionada == "Daily Viral Songs":
            sub_opcao_viral = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_viral")
            if sub_opcao_viral == "Global":
                display_chart(8, "Daily Viral Songs Global", "a música", "viral_songs_global", 'daily', 'Spotify')
            elif sub_opcao_viral == "Brasil":
                display_chart(9, "Daily Viral Songs Brasil", "a música", "viral_songs_brasil", 'daily', 'Spotify')

    elif spotify_charts_selection == "Weekly Charts":
        with st.sidebar.expander("Spotify Weekly", expanded=True):
            opcao_selecionada = st.radio("Selecione uma opção:", ["Weekly Top Songs", "Weekly Top Artists", "Weekly Top Albums"], key="weekly_menu_radio")

        if opcao_selecionada == "Weekly Top Songs":
            sub_opcao_songs_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_songs_weekly")
            if sub_opcao_songs_weekly == "Global":
                display_weekly_global_chart(6, "Weekly Top Songs Global", "a música", "weekly_songs_global")
            elif sub_opcao_songs_weekly == "Brasil":
                display_chart(7, "Weekly Top Songs Brasil", "a música", "weekly_songs_brasil", 'weekly', 'Spotify')
        elif opcao_selecionada == "Weekly Top Artists":
            sub_opcao_artists_weekly = st.radio("Selecione uma região:", ("Global", "Brasil"), key="sub_menu_artists_weekly")
            if sub_opcao_artists_weekly == "Global":
                display_weekly_global_chart(2, "Weekly Top Artists Global", "o artista", "weekly_artists_global")
            elif sub_opcao_artists_weekly == "Brasil":
                display_chart(3, "Weekly Top Artists Brasil", "o artista", "weekly_artists_brasil", 'weekly', 'Spotify')
        elif opcao_selecionada == "Weekly Top Albums":
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
    display_chart(sheet_index=12, section_title="Daily Top Songs Deezer", item_type="a música", key_suffix="songs_deezer", chart_type='daily', platform='Deezer')

elif plataforma_selecionada == "Amazon":
    display_chart(sheet_index=13, section_title="Daily Top Songs Amazon", item_type="a música", key_suffix="songs_amazon", chart_type='daily', platform='Amazon')

elif plataforma_selecionada == "Apple Music":
    display_chart(sheet_index=14, section_title="Daily Top Songs Apple Music", item_type="a música", key_suffix="songs_apple", chart_type='daily', platform='Apple Music')

st.write("---")
st.markdown("Desenvolvido com Python e Streamlit, este painel é uma ferramenta essencial para a análise de mercado musical. Os dados aqui apresentados refletem as tendências mais recentes, permitindo uma tomada de decisão estratégica e ágil para artistas e profissionais da indústria.")

st.markdown("---")
col1, col2 = st.columns([1, 4])

with col1:
    try:
        rodape_image = Image.open("habbla_rodape.jpg")
        st.image(rodape_image, width=110)
    except FileNotFoundError:
        st.write("Logo do rodapé não encontrada.")


with col2:
    st.markdown(
        """
        <div style='font-size: 12px; color: gray;'>
        Desenvolvido pela equipe de dados da <b>Habbla</b> | © 2025 Habbla Marketing<br>
        Versão 1.0.0 | Atualizado em: Setembro/2025<br>
        <a href="mailto:nil@habbla.ai">nil@habbla.ai</a> |
        <a href="https://vybbe.com.br" target="_blank">Site Institucional</a>
        </div>
        """,
        unsafe_allow_html=True
    )