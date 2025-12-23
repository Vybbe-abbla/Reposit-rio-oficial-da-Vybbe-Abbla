import os
import requests
import json
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
BASE_URL = "https://api.perplexity.ai"
MODEL_NAME = "sonar-pro"

def _format_date_for_prompt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")

def buscar_noticias(artista: str, data_inicio: datetime, data_fim: datetime):
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY não definido.")

    inicio_prompt = _format_date_for_prompt(data_inicio)
    fim_prompt = _format_date_for_prompt(data_fim)

    # Prompt otimizado para Deep Research (estilo Sonar-Pro)
    prompt = f"""
Você é um especialista em monitoramento de mídia. Realize uma pesquisa profunda sobre o artista "{artista}".
INTERVALO OBRIGATÓRIO: de {inicio_prompt} até {fim_prompt}.

TAREFA:
- Identifique shows específicos (nomes de eventos, locais, cidades), lançamentos e polêmicas no período.
- Priorize detalhes jornalísticos (ex: "Show no Natal do Chacon em Recife").
- Se não houver nada no período, relate a última atividade oficial conhecida no resumo_geral.

FORMATO DE SAÍDA (Retorne APENAS o JSON abaixo):
{{
  "resumo_geral": "Parágrafo narrativo detalhado com os fatos do período.",
  "noticias": [
    {{
      "titulo": "Título da notícia ou post",
      "descricao": "Detalhes contextuais com datas e locais",
      "url": "Link direto da fonte"
    }}
  ]
}}
"""

    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    body = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt.strip()}], "temperature": 0.2}

    response = requests.post(f"{BASE_URL}/chat/completions", json=body, headers=headers, timeout=60)
    response.raise_for_status()
    
    content = response.json()["choices"][0]["message"]["content"]

    # LIMPEZA DE MARKDOWN: Garante que o JSON seja processado corretamente sem aparecer texto bruto
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        parsed = json.loads(content)
        resumo = parsed.get("resumo_geral", "").strip()
        noticias = parsed.get("noticias", []) or []
        return resumo, noticias
    except json.JSONDecodeError:
        return content, [] # Fallback caso a API mande apenas texto