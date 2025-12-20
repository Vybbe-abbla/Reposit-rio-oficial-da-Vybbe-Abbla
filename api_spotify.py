# api_spotify.py

import os
import requests
from typing import Optional, Tuple

# ============================================================
# ATENÇÃO: preencha suas credenciais do Spotify aqui ou via
# variáveis de ambiente SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET.
# ============================================================
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


def get_spotify_token() -> str:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError(
            "SPOTIFY_CLIENT_ID ou SPOTIFY_CLIENT_SECRET não estão definidos. "
            "Preencha os valores em api_spotify.py ou via variáveis de ambiente."
        )

    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    response = requests.post(TOKEN_URL, data=data, auth=auth, timeout=30)
    response.raise_for_status()
    token_data = response.json()
    return token_data["access_token"]


def buscar_artista_spotify(nome_artista: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Retorna (image_url, spotify_url) do artista.
    """
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}

    params = {"q": nome_artista, "type": "artist", "limit": 1}

    response = requests.get(
        f"{SPOTIFY_API_BASE}/search",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    items = data.get("artists", {}).get("items", [])
    if not items:
        return None, None

    artist = items[0]
    images = artist.get("images", [])
    image_url = images[0]["url"] if images else None
    spotify_url = artist.get("external_urls", {}).get("spotify")

    return image_url, spotify_url
