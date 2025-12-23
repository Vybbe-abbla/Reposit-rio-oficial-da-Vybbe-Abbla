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


def montar_mensagem_whatsapp(resumos_por_artista, links_por_artista, data_inicio, data_fim):
    """
    Cria uma mensagem formatada com negritos, emojis e links para WhatsApp.
    """
    msg = []
    msg.append(f"*🚀 RESUMO DIÁRIO - MONITOR DE ARTISTAS*")
    msg.append(f"📅 Período: {data_inicio.strftime('%d/%m')} a {data_fim.strftime('%d/%m/%Y')}")
    msg.append("—" * 20)

    for artista, resumo in resumos_por_artista.items():
        # Cabeçalho do Artista
        msg.append(f"\n*🎵 {artista.upper()}*")
        
        # Resumo (Garante que não seja JSON e limpa espaços)
        if not resumo or "resumo_geral" in resumo:
            resumo = "Nenhuma menção relevante encontrada no período."
        
        msg.append(f"{resumo}")

        # Links/Notícias
        noticias = links_por_artista.get(artista, [])
        if noticias:
            msg.append("\n*Principais links:*")
            for n in noticias[:3]: # Limita a 3 links para não ficar gigante
                titulo = n.get('titulo', 'Link')
                url = n.get('url', '')
                if url:
                    msg.append(f"🔗 {titulo}: {url}")
        
        msg.append("\n" + "—" * 15)

    msg.append("\n_Gerado automaticamente pelo Painel de Monitoramento_")
    
    return "\n".join(msg)