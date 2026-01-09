import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import re
from dotenv import load_dotenv

# 1. Configurações de Estilo
st.set_page_config(layout="wide", page_title="Dashboard Musical 2025")

st.markdown("""
    <style>
    .rounded-img {
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #333;
    }
    .header-grid {
        display: grid; 
        grid-template-columns: 80px 3fr 2fr 2fr 2fr; 
        font-weight: bold; 
        color: #888;
        border-bottom: 1px solid #333; 
        padding: 10px 0;
    }
    .row-grid {
        display: grid; 
        grid-template-columns: 80px 3fr 2fr 2fr 2fr; 
        align-items: center; 
        padding: 15px 0; 
        border-bottom: 0.5px solid #222;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão Spotify
load_dotenv()
try:
    client_id = st.secrets["SPOTIPY_CLIENT_ID"]
    client_secret = st.secrets["SPOTIPY_CLIENT_SECRET"]
except:
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# 3. Carregamento do Dataset
@st.cache_data
def load_data():
    df = pd.read_excel("BD_Painel.xlsm", engine='openpyxl')
    df.columns = [str(c).strip() for c in df.columns] 
    return df

df_base = load_data()

artistas_lista = [
    "Xand Avião", "NATTAN", "Avine Vinny", "Léo Foguete", "Felipe Amorim",
    "Zé Cantor", "Jonas Esticado", "Guilherme Dantas", "Manim Vaqueiro",
    "Mari Fernandez", "Zé Vaqueiro", "Talita Mel", "Lipe Lucena"
]

# 4. Funções Auxiliares
def get_artist_data(name):
    results = sp.search(q=f'artist:{name}', type='artist', limit=1)
    items = results['artists']['items']
    return (items[0]['id'], items[0]['images'][0]['url']) if items else (None, None)

# 5. Interface Principal
st.title("🎵 Gestão de Lançamentos 2025")
tab_musica, tab_album = st.tabs(["📊 Músicas (Apenas do Arquivo)", "💿 Álbuns (Lançamentos)"])

with tab_musica:
    for artista in artistas_lista:
        aid, aimg = get_artist_data(artista)
        df_artista = df_base[df_base['Artista'].str.contains(artista, case=False, na=False)]
        
        if not df_artista.empty:
            col_h1, col_h2 = st.columns([1, 10])
            with col_h1:
                if aimg: st.markdown(f'<img src="{aimg}" class="rounded-img" width="70">', unsafe_allow_html=True)
            with col_h2: st.header(artista)

            st.markdown('<div class="header-grid"><div>Capa</div><div>Música</div><div>Álbum / Status</div><div>Streams</div><div>Lançamento</div></div>', unsafe_allow_html=True)

            for _, row in df_artista.iterrows():
                nome_musica = row['song']
                
                # Busca a música no Spotify para identificar o Álbum
                search_track = sp.search(q=f"track:{nome_musica} artist:{artista}", type="track", limit=1)
                
                t_img = ""
                album_status = "Não encontrado"
                
                if search_track['tracks']['items']:
                    track_info = search_track['tracks']['items'][0]
                    t_img = track_info['album']['images'][0]['url']
                    
                    # Identifica se é álbum ou single
                    album_type = track_info['album']['album_type']
                    if album_type == 'album':
                        album_status = track_info['album']['name']
                    else:
                        album_status = "Single"
                
                # Formatação de Streams e Data do Excel
                streams = f"{int(row['streams']):,}".replace(",", ".") if pd.notnull(row['streams']) else "---"
                try:
                    data_br = pd.to_datetime(row['Data de Lançamento']).strftime('%d/%m/%Y')
                except:
                    data_br = str(row['Data de Lançamento'])

                st.markdown(f"""
                <div class="row-grid">
                    <div><img src="{t_img}" class="rounded-img" width="50"></div>
                    <div style="font-weight:bold;">{nome_musica}</div>
                    <div style="color:#aaa;">{album_status}</div>
                    <div style="color:#1DB954; font-weight:bold;">{streams}</div>
                    <div style="color:#888;">{data_br}</div>
                </div>
                """, unsafe_allow_html=True)
            st.divider()

with tab_album:
    for artista in artistas_lista:
        aid, aimg = get_artist_data(artista)
        if aid:
            st.markdown(f'### <img src="{aimg}" class="rounded-img" width="45"> {artista}', unsafe_allow_html=True)
            
            albums = sp.artist_albums(aid, album_type='album')
            for alb in albums['items']:
                if "2025" in alb['release_date']:
                    c1, c2 = st.columns([1, 5])
                    with c1: st.image(alb['images'][0]['url'], width=120)
                    with c2:
                        st.write(f"**Álbum:** {alb['name']}")
                        st.write(f"**Lançamento:** {alb['release_date']}")
            st.write("---")