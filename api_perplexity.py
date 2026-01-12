import os
import requests
import re
import json
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
BASE_URL = "https://api.perplexity.ai"
MODEL_NAME = "sonar-pro"

def buscar_noticias(artista: str, data_inicio: datetime, data_fim: datetime, termos_especificos: str = ""):
    """
    Busca notícias utilizando a API Perplexity com suporte a termos de segmentação.
    """
    if not PERPLEXITY_API_KEY:
        return "Erro: PERPLEXITY_API_KEY não configurado.", []

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    inicio_p = data_inicio.strftime("%Y-%m-%d %H:%M")
    fim_p = data_fim.strftime("%Y-%m-%d %H:%M")

    prioridade = ""
    if termos_especificos:
        prioridade = f"\n⚠️ PRIORIDADE MÁXIMA: Pesquise especificamente sobre: {termos_especificos}."

    prompt = f"""
    Você é um analista de mídia para o grupo Vybbe. Monitore o artista "{artista}".
    {prioridade}
    BUSCA: Entre {inicio_p} e {fim_p}. 
    Tipos de conteúdo que devem ser PRIORITÁRIOS nesta busca geral:
    - Crises, polêmicas, términos de relacionamento, separações, escândalos.
    - Comunicados oficiais do artista ou da equipe.
    - Momentos importantes de carreira (prêmios, grandes feats, mudanças de equipe, etc.).
    - Anúncios de shows, turnês, lançamentos de músicas/clipes e parcerias.
    
    Traga fatos marcantes (vida pessoal, família, carreira).
    Se vazio no período, busque os últimos 3 dias. 

    Outras fontes que também podem ser consideradas:
    - Portais de notícia nacionais e regionais.
    - Instagram, X/Twitter, Facebook e outras plataformas de redes sociais.
    - Quando houver posts relevantes (por exemplo, anúncio de turnê ou nota de esclarecimento
      em Instagram ou X/Twitter), inclua pelo menos 1 ou 2 desses posts com o link direto.

    Regras importantes:
    - NÃO invente notícias.
    - Sempre retorne pelo menos 1 a 3 notícias recentes sobre o artista, se existirem na web

    RESPOSTA: Apenas JSON com "resumo_geral" (texto) e "noticias" (lista de objetos com titulo, descricao, url).

    """
    body = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt.strip()}]}

    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=body, headers=headers, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        # Extração robusta de JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            return parsed.get("resumo_geral", ""), parsed.get("noticias", [])
        return content.strip(), []
    except Exception as e:
        return f"Erro na API: {str(e)}", []