import streamlit as st
import pandas as pd
from datetime import date
import os
import glob
import re

st.set_page_config(page_title="Impulsionamento Instagram", layout="centered")

# pasta onde serão salvos os arquivos (ajuste se quiser)
base_dir = r"H:\Meu Drive\9.Power_Bi\2.Impulsionamentos\1.BD_Impsulsionamentos"
os.makedirs(base_dir, exist_ok=True)

# helpers
def save_df_with_index(df: pd.DataFrame, prefix: str, base_dir: str) -> str:
    """
    Salva `df` em base_dir com o nome prefix_NNN.xlsx onde NNN é índice incremental.
    Retorna o caminho completo do arquivo salvo.
    """
    pattern = os.path.join(base_dir, f"{prefix}_*.xlsx")
    files = glob.glob(pattern)
    max_idx = 0
    for f in files:
        m = re.search(fr"{re.escape(prefix)}_(\d+)\.xlsx$", os.path.basename(f))
        if m:
            idx = int(m.group(1))
            if idx > max_idx:
                max_idx = idx
    next_idx = max_idx + 1
    filename = f"{prefix}_{next_idx:03d}.xlsx"
    path = os.path.join(base_dir, filename)
    df.to_excel(path, index=False)
    return path

# lista fixa de artistas (pode manter como antes)
t_artista = pd.DataFrame({
    "Artista": [
        "Avine Vinny", "Felipe Amorim", "Guilherme Dantas", "Jonas Esticado",
        "Léo Foguete", "Lipe Lucena", "Manim Vaqueiro", "Mari Fernandes",
        "Nattan", "Talita Mel", "Xand Avião", "Zé Cantor", "Zé Vaqueiro"
    ]
})

# colunas padrão (reutilizáveis)
cols_canais = [
    "Data", "Canal", "Tema campanha", "Link Feed", "Artista",
    "R$ Valor campanha", "Data para coleta de dados",
    "Comentarios", "Curtidas", "Compartilhamentos", "Visualizações"
]

cols_influ = [
    "Data", "Influenciador", "Tema campanha", "Link Feed", "Artista",
    "R$ Valor campanha", "Data para coleta de dados",
    "Comentarios", "Curtidas", "Compartilhamentos", "Visualizações"
]

# inicializações em session_state
if "temas" not in st.session_state:
    st.session_state.temas = pd.DataFrame(columns=["Tema", "Artista"])

if "df_canais" not in st.session_state:
    st.session_state.df_canais = pd.DataFrame(columns=cols_canais)

if "df_influenciadores" not in st.session_state:
    st.session_state.df_influenciadores = pd.DataFrame(columns=cols_influ)

st.title("📊 Aplicação de Impulsionamento no Instagram")
st.markdown("Gerencie campanhas de **Canal** ou **Influenciador** com cadastro prévio de temas e artistas.")

st.markdown("---")
st.subheader("📝 Cadastro de Tema e Artista")
with st.form("form_tema", clear_on_submit=True):
    tema_novo = st.text_input("🎯 Tema da campanha")
    artista_novo = st.selectbox("🎤 Artista", options=t_artista["Artista"].tolist())
    submitted_tema = st.form_submit_button("✅ Cadastrar Tema")
    if submitted_tema:
        if tema_novo.strip() == "":
            st.warning("⚠️ O nome do tema não pode estar vazio.")
        elif tema_novo in st.session_state.temas["Tema"].values:
            st.warning("⚠️ Este tema já foi cadastrado.")
        else:
            novo_tema = {"Tema": tema_novo.strip(), "Artista": artista_novo}
            st.session_state.temas = pd.concat(
                [st.session_state.temas, pd.DataFrame([novo_tema])],
                ignore_index=True
            )
            st.success(f"Tema **{tema_novo}** cadastrado com artista **{artista_novo}**.")
            st.rerun()

# mostra temas cadastrados
if not st.session_state.temas.empty:
    st.dataframe(st.session_state.temas, use_container_width=True)
else:
    st.info("Nenhum tema cadastrado ainda.")

st.markdown("---")
tipo_campanha = st.radio("Selecione o tipo de campanha:", ("Canal", "Influenciador"))

if st.session_state.temas.empty:
    st.warning("⚠️ Cadastre ao menos um tema antes de registrar campanhas.")
else:
    if tipo_campanha == "Canal":
        st.info("Você selecionou **Canal**.")
        with st.form("form_canais", clear_on_submit=True):
            data = st.date_input("📅 Data", value=date.today())
            canal = st.text_input("📺 Canal")
            tema_escolhido = st.selectbox("🎯 Tema da campanha", options=st.session_state.temas["Tema"].tolist())
            artista = ""
            if tema_escolhido in st.session_state.temas["Tema"].values:
                artista = st.session_state.temas.loc[
                    st.session_state.temas["Tema"] == tema_escolhido, "Artista"
                ].values[0]
            st.text(f"🎤 Artista vinculado: {artista}")
            link = st.text_input("🔗 Link do Feed", placeholder="https://www.instagram.com/...")
            valor = st.number_input("💰 Valor da campanha (R$)", min_value=0.0, format="%.2f")
            data_coleta = st.date_input("📅 Data para coleta de dados", value=date.today())
            submitted_canais = st.form_submit_button("✅ Salvar Campanha Canal")


            if submitted_canais:
                novo_registro = {
                    "Data": data,
                    "Canal": canal,
                    "Tema campanha": tema_escolhido,
                    "Link Feed": link,
                    "Artista": artista,
                    "R$ Valor campanha": valor,
                    "Data para coleta de dados": data_coleta,
                    "Comentarios": "", "Curtidas": "", "Compartilhamentos": "", "Visualizações": ""
                }
                st.session_state.df_canais = pd.concat(
                    [st.session_state.df_canais, pd.DataFrame([novo_registro])],
                    ignore_index=True
                )
                st.success("Campanha por **Canal** salva com sucesso!")
                st.rerun()

    else:
        st.info("Você selecionou **Influenciador**.")
        with st.form("form_influenciadores", clear_on_submit=True):
            data = st.date_input("📅 Data", value=date.today(), key="data_inf")
            influenciador = st.text_input("👤 Influenciador")
            tema_escolhido = st.selectbox("🎯 Tema da campanha", options=st.session_state.temas["Tema"].tolist())
            artista = ""
            if tema_escolhido in st.session_state.temas["Tema"].values:
                artista = st.session_state.temas.loc[
                    st.session_state.temas["Tema"] == tema_escolhido, "Artista"
                ].values[0]
            st.text(f"🎤 Artista vinculado: {artista}")
            link = st.text_input("🔗 Link do Feed", placeholder="https://www.instagram.com/...")
            valor = st.number_input("💰 Valor da campanha (R$)", min_value=0.0, format="%.2f", key="valor_inf")
            data_coleta = st.date_input("📅 Data para coleta de dados", value=date.today(), key="data_coleta_inf")
            submitted_influenciadores = st.form_submit_button("✅ Salvar Campanha Influenciador")
            if submitted_influenciadores:
                novo_registro = {
                    "Data": data,
                    "Influenciador": influenciador,
                    "Tema campanha": tema_escolhido,
                    "Link Feed": link,
                    "Artista": artista,
                    "R$ Valor campanha": valor,
                    "Data para coleta de dados": data_coleta,
                    "Comentarios": "", "Curtidas": "", "Compartilhamentos": "", "Visualizações": ""
                }
                st.session_state.df_influenciadores = pd.concat(
                    [st.session_state.df_influenciadores, pd.DataFrame([novo_registro])],
                    ignore_index=True
                )
                st.success("Campanha por **Influenciador** salva com sucesso!")
                st.rerun()

st.markdown("---")
st.subheader("📊 Campanhas Registradas")
aba = st.radio("Escolha o tipo de campanhas para visualizar:", ["Canais", "Influenciadores"])

if aba == "Canais":
    st.dataframe(st.session_state.df_canais, use_container_width=True)
    if st.button("💾 Salvar campanhas de Canais"):
        if st.session_state.df_canais.empty:
            st.warning("Nada para salvar. O DataFrame de campanhas de canais está vazio.")
        else:
            path = save_df_with_index(st.session_state.df_canais, "campanhas_canais", base_dir)
            # limpa o dataframe após salvar
            st.session_state.df_canais = pd.DataFrame(columns=cols_canais)
            st.success(f"Arquivo salvo em: {path}")
            st.rerun()

else:
    st.dataframe(st.session_state.df_influenciadores, use_container_width=True)
    if st.button("💾 Salvar campanhas de Influenciadores"):
        if st.session_state.df_influenciadores.empty:
            st.warning("Nada para salvar. O DataFrame de campanhas de influenciadores está vazio.")
        else:
            path = save_df_with_index(st.session_state.df_influenciadores, "campanhas_influenciadores", base_dir)
            # limpa o dataframe após salvar
            st.session_state.df_influenciadores = pd.DataFrame(columns=cols_influ)
            st.success(f"Arquivo salvo em: {path}")
            st.rerun()

st.markdown("---")
col1, col2 = st.columns([1, 4])

with col1:
    st.image("habbla_rodape.jpg", width=110)

with col2:
    st.markdown(
        """
        <div style='font-size: 12px; color: gray;'>
            Desenvolvido pela equipe de dados da <b>Habbla</b> | © 2025 Habbla Marketing<br>
            Versão 1.0.0 | Atualizado em: Outubro/2025<br>
            <a href="mailto:nil@habbla.ai">nil@habbla.ai</a> |
            <a href="https://vybbe.com.br" target="_blank">Site Institucional</a>
        </div>
        """,
        unsafe_allow_html=True
    )
