# whatsapp_client.py

import requests


def enviar_whatsapp(mensagem: str, token: str, phone_id: str, destinatario: str):
    """
    Esqueleto para envio via WhatsApp Cloud API.
    """
    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def montar_mensagem_whatsapp(resumos_por_artista: dict, links_por_artista: dict) -> str:
    """
    Gera mensagem consolidada com resumos e principais notícias por artista.

    resumos_por_artista: {nome: resumo}
    links_por_artista: {nome: [ {"titulo": str, "url": str}, ... ]}
    """
    linhas = []
    linhas.append("Resumo de notícias dos artistas:\n")

    for artista, resumo in resumos_por_artista.items():
        linhas.append(f"*{artista}*")
        linhas.append(resumo.strip() or "Nenhuma notícia relevante encontrada no período.")

        noticias = links_por_artista.get(artista, [])
        if noticias:
            linhas.append("Principais matérias:")
            for n in noticias[:5]:
                titulo = n.get("titulo", "").strip() or "Matéria"
                url = n.get("url", "").strip()
                if url:
                    # Formato: Título – link
                    linhas.append(f"- {titulo} – {url}")
        linhas.append("")  # linha em branco

    return "\n".join(linhas).strip()
