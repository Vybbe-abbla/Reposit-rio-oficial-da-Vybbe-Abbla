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

# --- Funções de Carregamento ---
@st.cache_data
def load_data(sheet_index):
    creds_json = st.secrets.get("GOOGLE_SHEETS_CREDENTIALS") or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json: return pd.DataFrame()
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write(creds_json)
            path = f.name
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
        client = gspread.authorize(creds)
        planilha = client.open("2025_Charts")
        worksheet = planilha.get_worksheet(sheet_index)
        
        if sheet_index == 5:
            expected = ['DATA', 'Rank', 'uri', 'Artista', 'Música', 'source', 'peak_rank', 'previous_rank', 'days_on_chart', 'Corte charts', 'Data de Pico', 'Streams']
            data = worksheet.get_all_records(expected_headers=expected)
        else:
            data = worksheet.get_all_records()
        os.remove(path)
        return pd.DataFrame(data)
    except: return pd.DataFrame()

@st.cache_data
def get_spotify_info(query, search_type='track', artist_context=""):
    """Puxa o nome correto do álbum e a imagem via Spotify API."""
    client_id = st.secrets.get("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = st.secrets.get("SPOTIPY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET")
    if not client_id: return None, None
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        if search_type == 'artist':
            results = sp.search(q=f'artist:"{query}"', type='artist', limit=1)
            item = results['artists']['items'][0]
            return item['name'], item['images'][0]['url']
        elif search_type == 'album':
            results = sp.search(q=f'album:"{query}" artist:"{artist_context}"', type='album', limit=1)
            item = results['albums']['items'][0]
            return item['name'], item['images'][0]['url']
        else:
            primary_artist = artist_context.split(',')[0].strip()
            results = sp.search(q=f'track:"{query}" artist:"{primary_artist}"', type='track', limit=1)
            item = results['tracks']['items'][0]
            # Retorna Nome do Álbum e Imagem do Álbum
            return item['album']['name'], item['album']['images'][0]['url']
    except: return query, None

# --- UI do Aplicativo ---
st.title("📊 Overview Consolidado")

artistas = sorted(["Xand Avião", "NATTAN", "Mari Fernandez", "Avine Vinny", "Felipe Amorim", "Zé Vaqueiro", "Léo Foguete"])
col_sel, col_perfil = st.columns([2, 1])

with col_sel:
    artista_sel = st.selectbox("Selecione o Artista:", artistas)
    gerar = st.button(f"Analisar {artista_sel}", type="primary")

with col_perfil:
    _, img_art = get_spotify_info(artista_sel, 'artist')
    if img_art:
        st.markdown(f"""
            <div style="text-align: center;"> 
                <img src="{img_art}" style="border-radius: 50%; width: 130px; height: 130px; object-fit: cover; border: 3px solid #1DB954;"> 
                <p style="margin-top: 5px; font-weight: bold; font-size: 18px;">{artista_sel}</p> 
            </div>
            """, unsafe_allow_html=True)

if gerar:
    all_hits = []
    for idx, categoria in MAPA_CATEGORIAS.items():
        df = load_data(idx)
        if df.empty: continue
        
        df.columns = [str(c).upper().strip() for c in df.columns]
        art_col = 'ARTISTA' if 'ARTISTA' in df.columns else 'CRIADOR'
        if art_col not in df.columns: continue
        
        df_art = df[df[art_col].astype(str).str.contains(artista_sel, case=False, na=False)]
        if not df_art.empty:
            rank_col = 'RANK' if 'RANK' in df.columns else 'POSIÇÃO'
            best_idx = pd.to_numeric(df_art[rank_col], errors='coerce').idxmin()
            best = df_art.loc[best_idx]
            
            tipo = 'artist' if "Artists" in categoria or "Artistas" in categoria else \
                   ('album' if "Albums" in categoria or "Álbuns" in categoria else 'track')
            
            item_query = best.get('MÚSICA') or best.get('FAIXA') or best.get('VÍDEO') or best.get('ÁLBUM') or artista_sel
            
            # Puxa informações do Spotify
            album_nome, img_url = get_spotify_info(item_query, tipo, artista_sel)

            all_hits.append({
                "Rank": best[rank_col],
                "Item": item_query,
                "Album": album_nome if tipo != 'artist' else "",
                "Categoria": categoria,
                "Tempo": best.get('DAYS_ON_CHART') or best.get('WEEKS_ON_CHART') or 'N/A',
                "Streams": best.get('STREAMS') or best.get('VISUALIZAÇÕES SEMANAIS') or 'N/A',
                "Data": best.get('DATA DE PICO') or best.get('DATA') or 'N/A',
                "Img": img_url,
                "Tipo": tipo
            })

    if all_hits:
        st.write("---")
        h_cols = st.columns([0.5, 3, 0.7, 0.8, 1, 1.2])
        for col, h in zip(h_cols, ["#", "MÚSICA/FAIXA", "Pico", "Tempo", "Streams", "Data"]):
            col.markdown(f"<p style='font-weight: bold; color: #888;'>{h}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0;'>", unsafe_allow_html=True)

        for hit in sorted(all_hits, key=lambda x: x['Rank']):
            c = st.columns([0.5, 3, 0.7, 0.8, 1, 1.2])
            c[0].markdown(f"**{hit['Rank']}**")
            
            with c[1]:
                sc1, sc2 = st.columns([1, 4])
                if hit['Img']: sc1.image(hit['Img'], width=75)
                
                # Exibe Nome do Álbum se for Música
                label_album = f"<br><span style='color: gray; font-size: 12px;'>Álbum: {hit['Album']}</span>" if hit['Album'] else ""
                sc2.markdown(f"**{hit['Item']}**{label_album}\n\n<small style='color: #1DB954;'>{hit['Categoria']}</small>", unsafe_allow_html=True)
            
            c[2].write(hit['Rank'])
            c[3].write(hit['Tempo'])
            
            streams = hit['Streams']
            c[4].write(f"{int(streams):,}".replace(",", ".") if isinstance(streams, (int, float)) else streams)
            c[5].write(str(hit['Data']))
            st.markdown("<hr style='margin: 10px 0; border: 0.1px solid #333;'>", unsafe_allow_html=True)