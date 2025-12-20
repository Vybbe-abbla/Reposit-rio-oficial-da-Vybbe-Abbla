# app.py

import streamlit as st
from datetime import datetime, timedelta, time

from api_perplexity import buscar_noticias
from api_spotify import buscar_artista_spotify
from whatsapp_utils import montar_mensagem_whatsapp  # enviar_whatsapp se quiser usar


# Lista fixa de artistas
ARTISTAS_INICIAIS = [
    "Xand Avião",
    "NATTAN",
    "Avine Vinny",
    "Léo Foguete",
    "Felipe Amorim",
    "Zé Cantor",
    "Jonas Esticado",
    "Guilherme Dantas",
    "Manim Vaqueiro",
    "Mari Fernandez",
    "Zé Vaqueiro",
    "Talita Mel",
    "Lipe Lucena",
]


def init_session_state():
    if "artistas" not in st.session_state:
        st.session_state["artistas"] = ARTISTAS_INICIAIS.copy()

    if "data_inicio" not in st.session_state or "data_fim" not in st.session_state:
        hoje = datetime.today().date()
        st.session_state["data_fim"] = hoje
        st.session_state["data_inicio"] = hoje - timedelta(days=1)  # padrão 24h

    if "resumos_cache" not in st.session_state:
        st.session_state["resumos_cache"] = {}

    if "pagina_atual" not in st.session_state:
        st.session_state["pagina_atual"] = "principal"

    if "artista_selecionado" not in st.session_state:
        st.session_state["artista_selecionado"] = None

    if "mensagem_whatsapp" not in st.session_state:
        st.session_state["mensagem_whatsapp"] = ""


def pagina_configuracoes():
    st.sidebar.subheader("Configurações")

    st.sidebar.markdown("**Período de busca**")

    preset = st.sidebar.selectbox(
        "Selecione um período:",
        ["Últimas 24 horas", "Últimos 7 dias", "Último mês", "Intervalo de datas"],
        index=0,
    )

    hoje = datetime.today().date()

    if preset == "Intervalo de datas":
        intervalo = st.sidebar.date_input(
            "Selecione o intervalo:",
            (
                st.session_state.get("data_inicio", hoje - timedelta(days=1)),
                st.session_state.get("data_fim", hoje),
            ),
        )
        # Streamlit devolve uma tupla (data_inicio, data_fim)
        if isinstance(intervalo, tuple) and len(intervalo) == 2:
            data_inicio, data_fim = intervalo
        else:
            data_inicio = intervalo
            data_fim = intervalo
    elif preset == "Últimos 7 dias":
        data_fim = hoje
        data_inicio = hoje - timedelta(days=7)
    elif preset == "Último mês":
        data_fim = hoje
        data_inicio = hoje - timedelta(days=30)
    else:  # Últimas 24 horas
        data_fim = hoje
        data_inicio = hoje - timedelta(days=1)

    st.session_state["data_inicio"] = data_inicio
    st.session_state["data_fim"] = data_fim

    st.sidebar.write(
        f"Período atual: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
    )


def pagina_principal():
    st.title("Painel de Notícias de Artistas")

    st.write(
        "Selecione um artista para visualizar as notícias e postagens mais recentes "
        "no período configurado ao lado."
    )

    artistas = st.session_state["artistas"]
    cols = st.columns(3)

    for idx, artista in enumerate(artistas):
        col = cols[idx % 3]
        with col:
            st.subheader(artista)

            try:
                imagem_url, spotify_url = buscar_artista_spotify(artista)
            except Exception:
                imagem_url, spotify_url = None, None

            if imagem_url:
                st.image(imagem_url, use_container_width=True)
            else:
                st.write("Imagem não disponível.")

            if spotify_url:
                st.markdown(f"[Perfil no Spotify]({spotify_url})")

            if st.button("Ver notícias", key=f"btn_{artista}"):
                st.session_state["pagina_atual"] = "artista"
                st.session_state["artista_selecionado"] = artista
                st.rerun()


def pagina_artista():
    artista = st.session_state.get("artista_selecionado")
    if not artista:
        st.warning("Nenhum artista selecionado.")
        return

    st.markdown(f"### {artista}")

    try:
        imagem_url, spotify_url = buscar_artista_spotify(artista)
    except Exception as e:
        imagem_url, spotify_url = None, None
        st.error(f"Erro ao buscar dados do Spotify: {e}")

    if imagem_url:
        st.image(imagem_url, width=300)
    else:
        st.write("Imagem não disponível.")

    if spotify_url:
        st.markdown(f"[Ver artista no Spotify]({spotify_url})")

    st.markdown("---")

    data_inicio_date = st.session_state["data_inicio"]
    data_fim_date = st.session_state["data_fim"]

    st.write(
        f"Período de busca: **{data_inicio_date.strftime('%d/%m/%Y')}** até "
        f"**{data_fim_date.strftime('%d/%m/%Y')}**"
    )

    data_inicio_dt = datetime.combine(data_inicio_date, time.min)
    data_fim_dt = datetime.combine(data_fim_date, time.max)

    cache_key = (artista, str(data_inicio_dt), str(data_fim_dt))
    if cache_key in st.session_state["resumos_cache"]:
        resumo, noticias = st.session_state["resumos_cache"][cache_key]
    else:
        with st.spinner("Buscando notícias e postagens mais relevantes..."):
            try:
                resumo, noticias = buscar_noticias(
                    artista=artista,
                    data_inicio=data_inicio_dt,
                    data_fim=data_fim_dt,
                )
                st.session_state["resumos_cache"][cache_key] = (resumo, noticias)
            except Exception as e:
                st.error(f"Erro ao buscar notícias: {e}")
                resumo, noticias = "", []

    st.markdown("#### Resumo das principais menções")
    if resumo:
        st.write(resumo)
    else:
        st.write("Nenhuma informação relevante encontrada para esse período.")

    st.markdown("#### Lista de notícias e posts")
    if noticias:
        for i, n in enumerate(noticias, start=1):
            st.markdown(f"**{i}. {n['titulo']}**")
            if n["descricao"]:
                st.write(n["descricao"])
            if n["url"]:
                st.markdown(f"[Link para a fonte]({n['url']})")
            st.markdown("---")
    else:
        st.write("Nenhuma notícia encontrada.")

    if st.button("Voltar para o painel"):
        st.session_state["pagina_atual"] = "principal"
        st.rerun()


def secao_whatsapp():
    st.markdown("### Preparar resumo para WhatsApp")

    st.write(
        "Gere uma mensagem consolidada com os resumos e links dos artistas, "
        "pronta para colar em um grupo de WhatsApp."
    )

    artistas = st.session_state["artistas"]
    data_inicio_date = st.session_state["data_inicio"]
    data_fim_date = st.session_state["data_fim"]

    data_inicio_dt = datetime.combine(data_inicio_date, time.min)
    data_fim_dt = datetime.combine(data_fim_date, time.max)

    if st.button("Gerar mensagem consolidada"):
        resumos_por_artista = {}
        links_por_artista = {}

        with st.spinner("Gerando resumos para todos os artistas..."):
            for artista in artistas:
                cache_key = (artista, str(data_inicio_dt), str(data_fim_dt))
                if cache_key in st.session_state["resumos_cache"]:
                    resumo, noticias = st.session_state["resumos_cache"][cache_key]
                else:
                    try:
                        resumo, noticias = buscar_noticias(
                            artista=artista,
                            data_inicio=data_inicio_dt,
                            data_fim=data_fim_dt,
                        )
                        st.session_state["resumos_cache"][cache_key] = (resumo, noticias)
                    except Exception as e:
                        resumo, noticias = f"Erro ao buscar notícias: {e}", []

                resumos_por_artista[artista] = resumo
                # Aqui guardamos título + url para usar na mensagem do WhatsApp
                links_por_artista[artista] = [
                    {"titulo": n.get("titulo", ""), "url": n.get("url", "")}
                    for n in noticias
                    if n.get("url")
                ]

            mensagem = montar_mensagem_whatsapp(resumos_por_artista, links_por_artista)
            st.session_state["mensagem_whatsapp"] = mensagem

    if st.session_state.get("mensagem_whatsapp"):
        st.markdown("#### Mensagem pronta para envio")
        st.text_area(
            "Copie e cole no seu grupo de WhatsApp:",
            value=st.session_state["mensagem_whatsapp"],
            height=350,
        )


def main():
    st.set_page_config(page_title="Monitor de Notícias de Artistas", layout="wide")
    init_session_state()
    pagina_configuracoes()

    with st.sidebar:
        if st.button("Painel de artistas"):
            st.session_state["pagina_atual"] = "principal"
            st.rerun()

    if st.session_state["pagina_atual"] == "principal":
        pagina_principal()
    else:
        pagina_artista()

    st.markdown("---")
    secao_whatsapp()


if __name__ == "__main__":
    main()
