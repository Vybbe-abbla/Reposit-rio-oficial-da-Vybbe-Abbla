# api_perplexity.py

import os
import requests
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

BASE_URL = "https://api.perplexity.ai"
MODEL_NAME = "sonar-pro"


def _format_date_for_prompt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _format_date_for_filter(dt: datetime) -> str:
    return f"{dt.month}/{dt.day}/{dt.year}"


def buscar_noticias(artista: str, data_inicio: datetime, data_fim: datetime):
    """
    Busca notícias e posts de redes sociais relevantes sobre um artista
    SOMENTE dentro do intervalo de datas informado.
    """
    if not PERPLEXITY_API_KEY:
        raise ValueError(
            "PERPLEXITY_API_KEY não está definido. "
            "Preencha o valor em api_perplexity.py ou via variável de ambiente."
        )

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    inicio_prompt = _format_date_for_prompt(data_inicio)
    fim_prompt = _format_date_for_prompt(data_fim)

    inicio_filter = _format_date_for_filter(data_inicio)
    fim_filter = _format_date_for_filter(data_fim)

    prompt = f"""
Você é um assistente que monitora notícias e redes sociais de artistas musicais brasileiros.

Regras de PERÍODO (obrigatórias):
- Considere APENAS conteúdos publicados entre {inicio_prompt} e {fim_prompt}.
- NÃO use notícias ou posts publicados fora desse intervalo, mesmo que sejam muito relevantes.
- Se não encontrar quase nada dentro do intervalo, diga isso claramente no resumo e traga poucas notícias.

Tarefa:
- Pesquise as principais notícias e menções em redes sociais sobre o artista "{artista}"
  nesse intervalo de {inicio_prompt} até {fim_prompt}.
- Dê prioridade para crises, polêmicas, separações, escândalos, além de lançamentos, shows e parcerias.
- Considere fontes como portais de notícia, Instagram, TikTok, YouTube, X/Twitter, Facebook etc.
- Quando houver posts relevantes no Instagram ou X/Twitter, inclua pelo menos 1 ou 2 com link direto.

Formato DE SAÍDA (somente o JSON, sem texto extra):
{{
  "resumo_geral": "um parágrafo curto explicando o que houve com o artista no período",
  "noticias": [
    {{
      "titulo": "título da notícia ou post",
      "descricao": "breve descrição do conteúdo ou contexto",
      "url": "link da fonte original (portal ou rede social)"
    }}
  ]
}}
"""

    body = {
    "model": MODEL_NAME,
    "messages": [
        {
            "role": "user",
            "content": prompt.strip(),
        }
    ],
    # REMOVIDOS os filtros para evitar que zere a busca:
    # "search_after_date_filter": inicio_filter,
    # "search_before_date_filter": fim_filter,
}


    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json=body,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"]

    import json
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return content, []

    resumo = parsed.get("resumo_geral", "").strip()
    noticias_brutas = parsed.get("noticias", []) or []

    noticias = []
    for n in noticias_brutas:
        noticias.append(
            {
                "titulo": n.get("titulo") or "Sem título",
                "descricao": n.get("descricao") or "",
                "url": n.get("url") or "",
            }
        )

    return resumo, noticias
