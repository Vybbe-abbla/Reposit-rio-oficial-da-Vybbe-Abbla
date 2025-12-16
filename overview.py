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
from PIL import Image

# --- Configuração da Página ---
st.set_page_config(page_title='Vybbe Charts Overview', layout="wide", initial_sidebar_state="collapsed")

# --- Identificação de Categorias Detalhada ---
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

# --- Funções de Carregamento (Google & Spotify) ---
@st.cache_data
def load_data(sheet_index):
    # Lógica de conexão com Google Sheets usando segredos do Streamlit ou .env
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
        
        # Tratamento especial para Sheet 5 (Spotify Brasil)
        if sheet_index == 5:
            expected = ['DATA', 'Rank', 'uri', 'Artista', 'Música', 'source', 'peak_rank', 'previous_rank', 'days_on_chart', 'Corte charts', 'Data de Pico', 'Streams']
            data = worksheet.get_all_records(expected_headers=expected)
        else:
            data = worksheet.get_all_records()
            
        os.remove(path)
        return pd.DataFrame(data)
    except: return pd.DataFrame()

@st.cache_data
def get_spotify_image(query, search_type='track', artist_context=""):
    client_id = st.secrets.get("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = st.secrets.get("SPOTIPY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET")
    if not client_id: return None
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        if search_type == 'artist':
            results = sp.search(q=f'artist:"{query}"', type='artist', limit=1)
            return results['artists']['items'][0]['images'][0]['url']
        else:
            primary_artist = artist_context.split(',')[0].strip()
            results = sp.search(q=f'track:"{query}" artist:"{primary_artist}"', type='track', limit=1)
            return results['tracks']['items'][0]['album']['images'][0]['url']
    except: return None

# --- Interface do Usuário ---
st.title("📊 Overview Consolidado")

artistas = sorted(["Xand Avião", "NATTAN", "Mari Fernandez", "Avine Vinny", "Felipe Amorim", "Zé Vaqueiro", "Léo Foguete"])

# Seção de Perfil (Correção do erro de imagem HTML)
col_sel, col_perfil = st.columns([2, 1])

with col_sel:
    artista_sel = st.selectbox("Selecione o Artista:", artistas)
    gerar = st.button(f"Analisar {artista_sel}", type="primary")

with col_perfil:
    img_art = get_spotify_image(artista_sel, 'artist')
    if img_art:
        # HTML seguro para Streamlit Cloud
        st.markdown(
            f"""
            <div style="text-align: center;"> 
                <img src="{img_art}" style="border-radius: 50%; width: 130px; height: 130px; object-fit: cover; border: 3px solid #1DB954;"> 
                <p style="margin-top: 5px; font-weight: bold; font-size: 18px;">{artista_sel}</p> 
            </div>
            """, unsafe_allow_html=True
        )

if gerar:
    # Lógica de processamento de picos
    all_hits = []
    for idx, categoria in MAPA_CATEGORIAS.items():
        df = load_data(idx)
        if df.empty: continue
        
        # Identificação inteligente de colunas (Spotify vs YouTube)
        df.columns = [str(c).upper().strip() for c in df.columns]
        art_col = 'ARTISTA' if 'ARTISTA' in df.columns else 'CRIADOR'
        if art_col not in df.columns: continue
        
        df_art = df[df[art_col].astype(str).str.contains(artista_sel, case=False, na=False)]
        if not df_art.empty:
            rank_col = 'RANK' if 'RANK' in df.columns else 'POSIÇÃO'
            best = df_art.loc[pd.to_numeric(df_art[rank_col], errors='coerce').idxmin()]
            
            # Define se puxa imagem do artista ou da música
            eh_artista = "Artists" in categoria or "Artistas" in categoria
            
            all_hits.append({
                "Rank": best[rank_col],
                "Item": best.get('MÚSICA') or best.get('FAIXA') or best.get('VÍDEO') or artista_sel,
                "Categoria": categoria,
                "Tempo": best.get('DAYS_ON_CHART') or best.get('WEEKS_ON_CHART') or 'N/A',
                "Streams": best.get('STREAMS') or best.get('VISUALIZAÇÕES SEMANAIS') or 'N/A',
                "Data": best.get('DATA DE PICO') or best.get('DATA') or 'N/A',
                "EhArtista": eh_artista
            })

    if all_hits:
        st.write("---")
        # Cabeçalho da Tabela Otimizado (Removido "Anterior")
        h_cols = st.columns([0.5, 3, 0.7, 0.8, 1, 1.2])
        for col, h in zip(h_cols, ["#", "MÚSICA/FAIXA", "Pico", "Tempo", "Streams", "Data"]):
            col.markdown(f"<p style='font-weight: bold; color: #888;'>{h}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0;'>", unsafe_allow_html=True)

        for hit in sorted(all_hits, key=lambda x: x['Rank']):
            t_busca = 'artist' if hit['EhArtista'] else 'track'
            n_busca = artista_sel if hit['EhArtista'] else hit['Item']
            img_item = get_spotify_image(n_busca, t_busca, artista_sel)
            
            c = st.columns([0.5, 3, 0.7, 0.8, 1, 1.2])
            c[0].markdown(f"**{hit['Rank']}**")
            
            with c[1]:
                sc1, sc2 = st.columns([1, 4])
                if img_item: sc1.image(img_item, width=65)
                sc2.markdown(f"**{hit['Item']}**\n\n<small style='color: #1DB954;'>{hit['Categoria']}</small>", unsafe_allow_html=True)
            
            c[2].write(hit['Rank'])
            c[3].write(hit['Tempo'])
            
            # Formatação de Streams
            streams = hit['Streams']
            if isinstance(streams, (int, float)):
                c[4].write(f"{int(streams):,}".replace(",", "."))
            else:
                c[4].write(streams)
                
            c[5].write(str(hit['Data']))
            st.markdown("<hr style='margin: 10px 0; border: 0.1px solid #333;'>", unsafe_allow_html=True)
    else:
        st.info("Nenhum dado encontrado para o artista selecionado.")