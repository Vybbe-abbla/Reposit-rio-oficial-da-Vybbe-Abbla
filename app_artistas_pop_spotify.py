import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image

# Função auxiliar para formatar números sem usar o módulo locale
def format_number_br(number):
    """Formata um número com separador de milhar (ponto) no estilo brasileiro."""
    return f"{number:,}".replace(",", ".").replace(".0", "")

# Suas credenciais da API do Spotify
CLIENT_ID = '5552cff177d042fc9f221530ae8bde07'
CLIENT_SECRET = '5c40d521b4b44b8f875c34d67a712e0d'

# Configuração da autenticação
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                               client_secret=CLIENT_SECRET))
except Exception as e:
    st.error(f"Erro de autenticação: Verifique suas credenciais no código. Detalhes: {e}")
    st.stop()

st.set_page_config(layout="wide")

# --- Funções de busca com cache ---
@st.cache_data(show_spinner=False)
def get_spotify_data(artist_name):
    results = sp.search(q='artist:' + artist_name, type='artist', limit=1)
    if not results['artists']['items']:
        return None, None, None, None
    
    artist_info = results['artists']['items'][0]
    artist_id = artist_info['id']
    
    top_tracks_raw = sp.artist_top_tracks(artist_id, country='BR')
    top_tracks = {'tracks': top_tracks_raw['tracks'][:15]}
    
    artist_albums_info = sp.artist_albums(artist_id, album_type='album')
    albums_list = []
    for album in artist_albums_info['items']:
        album_full_info = sp.album(album['id'])
        albums_list.append(album_full_info)
    albums_df = pd.DataFrame(albums_list)
    albums_df = albums_df.sort_values(by='popularity', ascending=False)
    
    return artist_info, top_tracks, albums_df, artist_id

# Carrega a lista de artistas de um arquivo Excel
try:
    df_artistas = pd.read_excel("tabela_artistas.xlsx")
    lista_artistas = df_artistas['Artista'].tolist()
except FileNotFoundError:
    st.error("Arquivo 'tabela_artistas.xlsx' não encontrado. Por favor, crie-o na mesma pasta.")
    st.stop()

try:
    imagem_logo = Image.open('habbla.jpg')
    st.image(imagem_logo)
except FileNotFoundError:
    st.header("Logo 'habbla.jpg' não encontrada.")

st.title("Artistas e Álbuns do Spotify - Análise de Popularidade")
st.markdown("""**Vybbe Insights**
Análise estratégica de desempenho musical com dados do Spotify – Desenvolvido por Habbla.""")

# --- Checkboxes em Colunas (agora independentes) ---
col_cb1, col_cb2, col_cb3 = st.columns(3)
with col_cb1:
    show_top_albums = st.checkbox("Top Álbuns por Artista", value=True)
with col_cb2:
    show_artist_popularity = st.checkbox("Popularidade de Artistas")
with col_cb3:
    show_artist_details = st.checkbox("Pesquisar Detalhes de Artista Individualmente")

st.markdown("---")

if show_top_albums:
    st.subheader("Top Álbuns por Artista")
    st.markdown("Álbum mais popular de cada artista Vybbe, ordenado por popularidade.")
    
    top_albums_all_artists = []
    for artist_name in lista_artistas:
        with st.spinner(f"Buscando álbum de {artist_name}..."):
            artist_info, _, albums_df, _ = get_spotify_data(artist_name)
            if artist_info and not albums_df.empty:
                top_album = albums_df.iloc[0]
                top_albums_all_artists.append({
                    "Artista": artist_info['name'],
                    "Nome do Álbum": top_album['name'],
                    "Popularidade": top_album['popularity'],
                    "Imagem": top_album['images'][0]['url'],
                    "Lançamento": top_album['release_date']
                })
    
    df_top_albums = pd.DataFrame(top_albums_all_artists)
    df_top_albums = df_top_albums.sort_values(by='Popularidade', ascending=False)
    
    rank = 1
    for _, row in df_top_albums.iterrows():
        st.markdown("---")
        col1, col2, col3 = st.columns([0.1, 0.3, 1])
        with col1:
            st.metric(label=" ", value=f"{rank}")
        with col2:
            st.image(row['Imagem'], width=180)
        with col3:
            st.subheader(f"{row['Nome do Álbum']}")
            st.write(f"Artista: **{row['Artista']}**")
            st.write(f"Popularidade: **{row['Popularidade']}**")
            release_date_obj = datetime.strptime(row['Lançamento'], '%Y-%m-%d')
            release_date_br = release_date_obj.strftime('%d/%m/%Y')
            st.write(f"Lançamento: **{release_date_br}**")
        rank += 1

if show_artist_popularity:
    st.header("Popularidade de Artistas")
    st.markdown("Popularidade dos artistas da sua lista, ordenado do maior para o menor.")
    
    artists_data_list = []
    for artist_name in lista_artistas:
        with st.spinner(f"Carregando informações de {artist_name}..."):
            artist_info, _, albums_df, _ = get_spotify_data(artist_name)
            if artist_info:
                followers_formatted = format_number_br(artist_info['followers']['total'])
                artists_data_list.append({
                    "Artista": artist_info['name'],
                    "Popularidade": artist_info['popularity'],
                    "Seguidores": followers_formatted,
                    "Álbuns": len(albums_df),
                    "Imagem": artist_info['images'][0]['url'] if artist_info['images'] else None
                })
    
    df_artists_data = pd.DataFrame(artists_data_list)
    df_artists_data = df_artists_data.sort_values(by='Popularidade', ascending=False)
    
    rank = 1
    for _, row in df_artists_data.iterrows():
        st.markdown("---")
        col1, col2, col3 = st.columns([0.1, 0.3, 1])
        with col1:
            st.metric(label=" ", value=f"{rank}")
        with col2:
            if row['Imagem']:
                st.image(row['Imagem'], width=180)
        with col3:
            st.subheader(f"{row['Artista']}")
            st.write(f"Popularidade: **{row['Popularidade']}**")
            st.write(f"Seguidores: **{row['Seguidores']}**")
            st.write(f"Álbuns: **{row['Álbuns']}**")
        rank += 1

if show_artist_details:
    st.subheader("Pesquisar Detalhes de Artista Individualmente")
    artist_name_selected = st.selectbox("Selecione um artista para ver mais detalhes", options=lista_artistas)
    
    if artist_name_selected:
        artist_info, top_tracks, albums_df, _ = get_spotify_data(artist_name_selected)
    
        if artist_info:
            col1, col2 = st.columns([1, 2])
            with col1:
                if artist_info['images']:
                    st.image(artist_info['images'][0]['url'], width=300)
                else:
                    st.write("Imagem não disponível.")
            
            with col2:
                st.header(artist_info['name'])
                st.metric("Popularidade", artist_info['popularity'])
                followers_formatted = format_number_br(artist_info['followers']['total'])
                st.metric("Seguidores", followers_formatted)
                st.write(f"**Gêneros:** {', '.join(artist_info['genres'])}")
    
            st.markdown("---")
            
            st.header(f"10 Músicas Mais Populares de {artist_info['name']}")
            top_tracks_list = []
            for track in top_tracks['tracks']:
                track_name_shortened = track['name'].split('/')[0].strip()
                top_tracks_list.append({
                    "Música": track_name_shortened,
                    "Popularidade": track['popularity'],
                    "Álbum": track['album']['name']
                })
            top_tracks_df = pd.DataFrame(top_tracks_list)
            top_tracks_df = top_tracks_df.sort_values(by='Popularidade', ascending=True)
            
            fig = px.bar(
                top_tracks_df,
                x='Popularidade',
                y='Música',
                title=f"Gráfico de Popularidade das Músicas de {artist_info['name']}",
                width=1150,
                height=500,
                hover_data=['Música', 'Popularidade'],
                color='Popularidade',
                text_auto=True,
                orientation='h',
                color_continuous_scale='Mint'
            )
            st.plotly_chart(fig)
            
            st.markdown("---")
    
            st.header(f"Explorar Álbuns de {artist_info['name']}")
            
            album_options = albums_df['name'].tolist()
            album_name_selected = st.selectbox("Selecione um álbum para ver as músicas", options=album_options)
            
            if album_name_selected:
                album_id_selected = albums_df.loc[albums_df['name'] == album_name_selected, 'id'].iloc[0]
                album_full_info = albums_df.loc[albums_df['id'] == album_id_selected].iloc[0]
                
                st.markdown("---")
                col3, col4 = st.columns([1, 2])
                with col3:
                    st.image(album_full_info['images'][0]['url'], width=300)
                with col4:
                    st.subheader(album_full_info['name'])
                    st.write(f"**Popularidade:** {album_full_info['popularity']}")
                    release_date_obj = datetime.strptime(album_full_info['release_date'], '%Y-%m-%d')
                    release_date_br = release_date_obj.strftime('%d/%m/%Y')
                    st.write(f"**Lançamento:** {release_date_br}")
    
                st.subheader(f"Músicas de {album_name_selected}")
                tracks_info = sp.album_tracks(album_id_selected)
                
                tracks_list = []
                for track in tracks_info['items']:
                    track_full_info = sp.track(track['id'])
                    track_name_shortened = track['name'].split('/')[0].strip()
                    tracks_list.append({
                        "Música": track_name_shortened,
                        "Popularidade": track_full_info['popularity']
                    })
                tracks_df = pd.DataFrame(tracks_list)
                tracks_df = tracks_df.sort_values(by='Popularidade', ascending=True)
                
                fig2 = px.bar(
                    tracks_df,
                    x='Popularidade',
                    y='Música',
                    title=f"Gráfico de Popularidade das Músicas de {album_name_selected}",
                    width=1150,
                    height=650,
                    hover_data=['Música', 'Popularidade'],
                    color='Popularidade',
                    text_auto=True,
                    orientation='h',
                    color_continuous_scale='Mint'
                )
                st.plotly_chart(fig2)

st.markdown("---")
col1, col2 = st.columns([1, 4])

with col1:
    st.image("habbla_rodape.jpg", width=110)

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