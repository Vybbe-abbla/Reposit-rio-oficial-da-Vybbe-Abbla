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
    # Formato aceito pelos filtros de data da Sonar: M/D/YYYY
    # Docs: search_after_date / search_before_date. [web:41][web:45]
    return dt.strftime("%m/%d/%Y")


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

Regras de período (OBRIGATÓRIO):
- Considere APENAS conteúdos publicados entre {inicio_prompt} e {fim_prompt}.
- NÃO use notícias ou posts publicados fora desse intervalo, mesmo que sejam muito relevantes.
- Se a maioria das notícias for antiga (por exemplo, 2021) e o período for 2025, você deve ignorá-las.
- Se não encontrar nada dentro do intervalo, diga claramente que há "pouca ou nenhuma informação no período especificado".

Contexto:
- Eventos de crise, polêmica ou impacto na imagem do artista são prioridade.
- Exemplos: separação, divórcio, brigas públicas, acusações, cancelamento de shows,
  problemas de saúde, polêmicas em entrevistas, controvérsias nas redes sociais etc.
- Um caso recente que NÃO pode ser ignorado quando estiver dentro do intervalo é a separação
  de Zé Vaqueiro e Ingra Soares no fim de novembro de 2025, amplamente noticiada.

Tarefa:
- Pesquise as principais notícias e menções em redes sociais sobre o artista "{artista}"
  SOMENTE no período de {inicio_prompt} até {fim_prompt}.
- Dê prioridade máxima para crises, polêmicas, términos de relacionamento, separações
  e escândalos que afetem a imagem do artista.
- Em seguida, inclua lançamentos, clipes, anúncios de shows, parcerias, prêmios e outros fatos relevantes.
- Considere fontes como: portais de notícia, Instagram, TikTok, YouTube, X/Twitter,
  Facebook e outras plataformas de redes sociais.
- Quando houver posts relevantes em alta no Instagram ou X/Twitter sobre o tema,
  inclua pelo menos 1 ou 2 desses posts com o link direto para o post.
- Responda em português do Brasil.

Formato de saída (JSON em texto, SEM explicações adicionais, apenas o objeto JSON):
{{
  "resumo_geral": "um parágrafo curto resumindo o que houve com o artista no período, enfatizando crises/polêmicas se houver",
  "noticias": [
    {{
      "titulo": "título da notícia ou post",
      "descricao": "breve descrição do conteúdo ou contexto, explicando se é crise, polêmica, separação etc.",
      "url": "link da fonte original (portal ou rede social, como Instagram ou X/Twitter)"
    }}
  ]
}}

Instruções finais:
- Inclua somente links reais e completos (https...) que estejam dentro do intervalo de datas.
- Se não houver praticamente nada no período, reduza a lista de notícias e explique isso no resumo.
"""


    body = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt.strip(),
            }
        ],
        # Filtros reais de data da Sonar (por data de publicação). [web:41][web:45]
        "search_after_date": inicio_filter,
        "search_before_date": fim_filter,
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
