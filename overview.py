import pandas as pd
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import tempfile
import numpy as np

# --- Configuração Inicial ---
st.set_page_config(page_title='Vybbe Charts Overview', layout="wide", initial_sidebar_state="collapsed")

load_dotenv()

try:
    import pytz
    TZ = pytz.timezone('America/Sao_Paulo')
except ImportError:
    TZ = None

# --- Mapeamento Detalhado de Categorias ---
MAPA_CATEGORIAS = {
    0: "Spotify | Daily Top Artists Global",
    1: "Spotify | Daily Top Artists Brasil",
    2: "Spotify | Weekly Top Artists Global",
    3: "Spotify | Weekly Top Artists Brasil",
    4: "Spotify | Daily Top Songs Global",
    5: "Spotify | Daily Top Songs Brasil",
    6: "Spotify | Weekly Top Songs Global",
    7: "Spotify | Weekly Top Songs Brasil",
    8: "Spotify | Daily Viral Songs Global",
    9: "Spotify | Daily Viral Songs Brasil",
    10: "Spotify | Weekly Top Albums Global",
    11: "Spotify | Weekly Top Albums Brasil",
    12: "Deezer | Daily Top Songs",
    13: "Amazon | Daily Top Songs",
    14: "Apple Music | Daily Top Songs",
    15: "YouTube | Top Artistas Semanal Brasil",
    16: "YouTube | Top Faixas Semanal Brasil",
    17: "YouTube | Top Clipes Semanal Brasil",
    18: "YouTube | Top Vídeos Diários Brasil",
    19: "YouTube | Top Shorts Diários Brasil"
}

# --- Carregamento de Dados ---
@st.cache_data
def load_data(sheet_index):
    google_sheets_creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not google_sheets_creds_json: return pd.DataFrame()
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_creds:
            temp_creds.write(google_sheets_creds_json)
            temp_path = temp_creds.name
        creds = ServiceAccountCredentials.from_json_keyfile_name(temp_path, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        planilha = client.open(title="2025_Charts")
        worksheet = planilha.get_worksheet(sheet_index)
        
        if sheet_index == 5:
            expected_headers = ['DATA', 'Rank', 'uri', 'Artista', 'Música', 'source', 'peak_rank', 'previous_rank', 'days_on_chart', 'Corte charts', 'Data de Pico', 'Streams']
            data = worksheet.get_all_records(expected_headers=expected_headers)
        else:
            data = worksheet.get_all_records()
            
        os.remove(temp_path)
        return pd.DataFrame(data)
    except: return pd.DataFrame()

# --- Busca de Imagens (Spotify API) ---
@st.cache_data
def get_spotify_image(query_name, search_type='track', artist_context=""):
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    if not SPOTIPY_CLIENT_ID: return None
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))
        if search_type == 'artist':
            results = sp.search(q=f'artist:"{query_name}"', type='artist', limit=1)
            if results['artists']['items']: return results['artists']['items'][0]['images'][0]['url']
        else:
            primary_artist = artist_context.split(',')[0].strip()
            results = sp.search(q=f'track:"{query_name}" artist:"{primary_artist}"', type='track', limit=1)
            if results['tracks']['items']: return results['tracks']['items'][0]['album']['images'][0]['url']
    except: pass
    return None

# --- Processamento Robusto do Overview ---
def processar_picos(artista_nome):
    indices = list(MAPA_CATEGORIAS.keys())
    resultados = []
    
    for idx in indices:
        df = load_data(idx)
        if df.empty: continue
        
        cols_norm = {str(c).upper().strip(): c for c in df.columns}
        art_col = cols_norm.get('ARTISTA') or cols_norm.get('CRIADOR')
        if not art_col: continue
        
        df_artista = df[df[art_col].astype(str).str.contains(artista_nome, case=False, na=False)].copy()
        
        if not df_artista.empty:
            rank_col = cols_norm.get('RANK') or cols_norm.get('POSIÇÃO') or cols_norm.get('POSICAO')
            if not rank_col: continue
            
            df_artista[rank_col] = pd.to_numeric(df_artista[rank_col], errors='coerce')
            df_artista = df_artista.dropna(subset=[rank_col])
            if df_artista.empty: continue
            
            melhor_registro = df_artista.loc[df_artista[rank_col].idxmin()]
            
            # Identificação se é categoria de ARTISTA ou MÚSICA
            categoria_str = MAPA_CATEGORIAS.get(idx, "Streaming")
            eh_categoria_artista = "Artists" in categoria_str or "Artistas" in categoria_str
            
            nome_col = cols_norm.get('MÚSICA') or cols_norm.get('MUSICA') or cols_norm.get('FAIXA') or \
                       cols_norm.get('VÍDEO') or cols_norm.get('VIDEO') or cols_norm.get('ÁLBUM') or \
                       cols_norm.get('ALBUM') or art_col # Fallback para o próprio nome do artista se for chart de artista
            
            nome_item = melhor_registro.get(nome_col, artista_nome)
            streams_col = cols_norm.get('STREAMS') or cols_norm.get('VISUALIZAÇÕES SEMANAIS')
            data_pico_col = cols_norm.get('DATA DE PICO') or cols_norm.get('DATA DO PICO') or cols_norm.get('DATA')

            resultados.append({
                "Categoria": categoria_str,
                "Música/Item": nome_item,
                "Pico": melhor_registro[rank_col],
                "Tempo": melhor_registro.get('days_on_chart', melhor_registro.get('Weeks_on_chart', 'N/A')),
                "Streams": melhor_registro.get(streams_col, 'N/A'),
                "Data": melhor_registro.get(data_pico_col, 'N/A'),
                "EhArtista": eh_categoria_artista
            })
    return pd.DataFrame(resultados)

# --- Interface ---
st.title("📊 Overview Consolidado de Performance")

artistas_vybbe = sorted(["Xand Avião", "NATTAN", "Mari Fernandez", "Avine Vinny", "Felipe Amorim", "Zé Vaqueiro", "Léo Foguete", "Guilherme Dantas", "Jonas Esticado", "Manim Vaqueiro", "Talita Mel", "Lipe Lucena", "Zé Cantor"])

# Topo: Selectbox e Imagem do Artista
col_selecao, col_imagem_artista = st.columns([2, 1])

with col_selecao:
    artista_sel = st.selectbox("Selecione o Artista para Análise:", artistas_vybbe)
    btn_gerar = st.button(f"🔍 Gerar Relatório de Performance para {artista_sel}", type="primary")

with col_imagem_artista:
    url_art = get_spotify_image(artista_sel, search_type='artist')
    if url_art:
        st.markdown(f"""
            <div style="text-align: center;">
                <img src="{url_art}" style="border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 3px solid #1DB954;">
                <p style="margin-top: 5px; font-weight: bold;">{artista_sel}</p>
            </div>
        """, unsafe_allow_html=True)

if btn_gerar:
    df_resumo = processar_picos(artista_sel)
    
    if not df_resumo.empty:
        st.write("---")
        header_cols = st.columns([0.5, 3, 0.7, 0.8, 1, 1.2])
        headers = ["#", "MÚSICA/FAIXA", "Pico", "Tempo", "Streams", "Data de Pico"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"<p style='font-weight: bold; color: #888;'>{h}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0;'>", unsafe_allow_html=True)

        df_resumo = df_resumo.sort_values(by='Pico')

        for _, row in df_resumo.iterrows():
            # Lógica de Imagem: Se for categoria de artista, puxa imagem do artista. Se não, puxa do álbum/track.
            tipo_busca = 'artist' if row['EhArtista'] else 'track'
            nome_busca = artista_sel if row['EhArtista'] else row['Música/Item']
            
            img_item = get_spotify_image(nome_busca, search_type=tipo_busca, artist_context=artista_sel)
            
            c = st.columns([0.5, 3, 0.7, 0.8, 1, 1.2])
            
            # Rank
            c[0].markdown(f"<p style='font-size: 20px; font-weight: bold;'>{int(row['Pico'])}</p>", unsafe_allow_html=True)
            
            # Item e Categoria Detalhada
            with c[1]:
                sub_c = st.columns([1, 4])
                if img_item: sub_c[0].image(img_item, width=75)
                else: sub_c[0].markdown("🖼️")
                
                # Exibe a categoria completa (ex: Spotify | Daily Top Songs Brasil)
                sub_c[1].markdown(f"**{row['Música/Item']}**\n\n<small style='color: #1DB954;'>{row['Categoria']}</small>", unsafe_allow_html=True)
            
            c[2].write(int(row['Pico']))
            c[3].write(row['Tempo'])
            
            # Streams Formatados
            streams = row['Streams']
            try:
                c[4].write(f"{int(float(str(streams).replace('.','').replace(',',''))):,}".replace(",", "."))
            except:
                c[4].write(streams)
                
            c[5].write(row['Data'])
            st.markdown("<hr style='margin: 10px 0; border: 0.1px solid #333;'>", unsafe_allow_html=True)
    else:
        st.info(f"Nenhum dado encontrado para **{artista_sel}** nos charts monitorados.")