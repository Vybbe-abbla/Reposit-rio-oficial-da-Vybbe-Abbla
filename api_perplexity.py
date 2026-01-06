# api_perplexity.py

import os
import json
from datetime import datetime

import requests
import re
import json

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
    (Busca geral: não é exclusiva de crise, mas dá prioridade a temas mais relevantes.)
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
Você é um assistente que monitora notícias e redes sociais de artistas musicais brasileiros do grupo Vybbe.

Período definido pelo usuário:
- Somente considere conteúdos publicados entre {inicio_prompt} e {fim_prompt}.
- Se houver QUALQUER notícia, nota, matéria ou post relevante nesse intervalo,
  você DEVE listar esses itens, mesmo que sejam poucos.

Artista alvo:
- "{artista}"

Tipos de conteúdo que devem ser PRIORITÁRIOS nesta busca geral:
- Crises, polêmicas, términos de relacionamento, separações, escândalos.
- Comunicados oficiais do artista ou da equipe.
- Anúncios de shows, turnês, lançamentos de músicas/clipes e parcerias.
- Momentos importantes de carreira (prêmios, grandes feats, mudanças de equipe, etc.).

FONTES PRIORITÁRIAS (quando houver notícias sobre o artista nelas):
SITES/PORTAIS:
- https://hugogloss.uol.com.br/
- https://portalleodias.com/
- https://palcopop.com/
- https://portaldosfamosos.com.br/
- https://www.purepeople.com.br/
- https://www.purepeople.com.br/noticias/1
- https://billboard.com.br/
- https://www.terra.com.br/diversao/gente/
- https://alfinetei.com.br/
- https://veja.abril.com.br/noticias-sobre/musica-brasileira/
- https://www.areavip.com.br/
- https://fortal.com.br/
- https://www.threads.com/

PERFIS / PÁGINAS NO INSTAGRAM (considere também notícias/fofocas replicadas em portais):
- @gossipdodia
- @redefrancesfm
- @quem
- @portaldosartistasoficial
- @hugogloss
- @segueacami
- @purepeoplebrasil
- @danielneblina
- @pbtododia
- @fluxodamusica
- @gossipdafama
- @billboardbr
- @ielcast
- @subcelebrities
- @portaldiario
- @ahoradavenenosa
- @karllos_kosta
- @blogsocial1
- @tvjornalsbt
- @ondetempe
-@neews_press
-@jornalextra
-@acerteiproducoes
-@vemfestejarfortaleza


Outras fontes que também podem ser consideradas:
- Portais de notícia nacionais e regionais.
- Instagram, TikTok, YouTube, X/Twitter, Facebook e outras plataformas de redes sociais.
- Quando houver posts relevantes (por exemplo, anúncio de turnê ou nota de esclarecimento
  em Instagram ou X/Twitter), inclua pelo menos 1 ou 2 desses posts com o link direto.

Regras importantes:
- NÃO invente notícias.
- NÃO use conteúdos fora do intervalo de {inicio_prompt} a {fim_prompt}.
- Se encontrar notícias de datas fora do período, ignore essas e tente achar algo dentro.
- Apenas se realmente não houver nada relevante nesse período, diga isso claramente
  no "resumo_geral" e deixe a lista de "noticias" vazia.

Formato de saída (apenas o JSON, sem texto extra):
{{
  "resumo_geral": "um parágrafo curto explicando o que houve com o artista no período (ou que quase nada foi encontrado)",
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
            {"role": "user", "content": prompt.strip()}
        ],
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

    try:
        # Tenta extrair o bloco JSON de dentro do texto (caso a IA mande conversa fiada)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content_json = json_match.group(0)
            parsed = json.loads(content_json)
            resumo = parsed.get("resumo_geral", "").strip()
            noticias_brutas = parsed.get("noticias", []) or []
        else:
            # Se não achar JSON, assume que o texto todo é o resumo
            resumo = content.strip()
            noticias_brutas = []
            
    except Exception:
        # Fallback total
        resumo = content.strip()
        noticias_brutas = []

    # Limpeza final: Se o resumo ainda contiver chaves de JSON por erro, removemos
    resumo = re.sub(r'\{.*"resumo_geral":\s*"|",\s*"noticias":.*\}', '', resumo, flags=re.DOTALL)

    return resumo, noticias_brutas