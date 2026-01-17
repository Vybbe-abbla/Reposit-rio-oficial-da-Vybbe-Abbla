import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image
from app_streams import load_data, format_br_number, TZ

def render_comparativo():
     
    rodape_image = Image.open('habbla_rodape.jpg')
    st.image(rodape_image, width=110)

    st.write("---")

    st.header("📊 Comparativo de Performance")

    st.markdown("""
    Bem-vindo à ferramenta de **Inteligência Competitiva**. Este módulo permite:
    * **Comparar Performance Temporal:** Analise até 3 músicas simultaneamente no Ranking ou Streams.
    * **Análise de Lançamento:** O gráfico de barras foca no impacto inicial (primeiro registro) de cada faixa.
    * **Filtros Personalizados:** Ajuste o período para identificar tendências e picos de audiência.
    """)

    st.write("---")
    
    df = load_data(5)
    
    if df.empty:
        st.error("Não foi possível carregar os dados da planilha.")
        return

    # Padronização de Colunas e Tipagem
    date_col = 'DATA' if 'DATA' in df.columns else 'Data'
    df[date_col] = pd.to_datetime(df[date_col], format="%d/%m/%Y")
    
    # Limpeza e conversão de Streams para numérico
    df['Streams_Num'] = df['Streams'].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False)
    df['Streams_Num'] = pd.to_numeric(df['Streams_Num'], errors='coerce')
    # Criar coluna formatada para exibição (padrão BR)
    df['y_axis_formatted'] = df['Streams_Num'].apply(lambda x: format_br_number(x))

    # 2. Filtros de Seleção de Músicas
    st.markdown("### Selecione as músicas para comparação")
    qtd_comparacao = st.radio("Quantidade de músicas para comparar:", [2, 3], index=0, horizontal=True)
    
    musicas_disponiveis = sorted(df['Música'].unique())
    col_sel1, col_sel2, col_sel3 = st.columns(3)
    
    with col_sel1:
        musica1 = st.selectbox("Música 1", musicas_disponiveis, index=0)
    with col_sel2:
        musica2 = st.selectbox("Música 2", musicas_disponiveis, index=min(1, len(musicas_disponiveis)-1))
    with col_sel3:
        musica3 = st.selectbox("Música 3", musicas_disponiveis, index=min(2, len(musicas_disponiveis)-1)) if qtd_comparacao == 3 else None

    lista_selecionada = [m for m in [musica1, musica2, musica3] if m is not None]

    # 3. Filtro de Intervalo Temporal
    df_temp = df[df['Música'].isin(lista_selecionada)]
    min_date_available = df_temp[date_col].min().date()
    max_date_available = df_temp[date_col].max().date()

    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Data de Início", value=min_date_available, min_value=min_date_available, max_value=max_date_available)
    with c2:
        end_date = st.date_input("Data de Fim", value=max_date_available, min_value=min_date_available, max_value=max_date_available)

    # Filtragem dos dados para o Gráfico de Linha
    df_filtered = df_temp[
        (df_temp[date_col].dt.date >= start_date) & 
        (df_temp[date_col].dt.date <= end_date)
    ].copy()

    # 4. GRÁFICO DE LINHA (Performance Temporal)
    metric_choice = st.radio("Tipo de visualização (Gráfico de Linha):", ["Ranking", "Streams"], horizontal=True)
    
    y_axis = "Rank" if metric_choice == "Ranking" else "Streams_Num"
    y_label = "Posição no Ranking" if metric_choice == "Ranking" else "Número de Streams"
    text_col = "Rank" if metric_choice == "Ranking" else "y_axis_formatted"

    fig_line = px.line(
        df_filtered, 
        x=date_col, 
        y=y_axis, 
        color='Música',
        text=text_col, # CORREÇÃO: Torna os valores visíveis sobre os pontos
        line_shape='spline',
        markers=True,
        title=f"Evolução de {y_label}"
    )

    fig_line.update_traces(textposition='top center')
    
    if metric_choice == "Ranking":
        fig_line.update_layout(yaxis=dict(autorange="reversed", title=y_label))
    else:
        fig_line.update_layout(yaxis=dict(title=y_label))

    fig_line.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_line, use_container_width=True)

    # 5. GRÁFICO DE BARRAS (Streams no Primeiro Registro)
    st.write("---")
    st.subheader("🚀 Streams no Primeiro Dia de Registro")
    
    # Lógica: Pegar o primeiro registro (data mínima) de cada música dentro do filtro selecionado
    df_primeiro_dia = df_filtered.sort_values(date_col).groupby('Música').head(1).copy()
    
    fig_bar = px.bar(
        df_primeiro_dia,
        x='Música',
        y='Streams_Num',
        color='Música',
        text='y_axis_formatted',
        title="Comparativo de Lançamento (Primeiro dia detectado no período)",
        labels={'Streams_Num': 'Streams', 'Música': 'Música'}
    )
    
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(showlegend=False, yaxis_title="Streams")
    
    # Adiciona a data de registro no hover para clareza
    fig_bar.update_traces(hovertemplate="<b>%{x}</b>Streams: %{text}")

    st.plotly_chart(fig_bar, use_container_width=True)

if __name__ == "__main__":
    st.set_page_config(page_title='Vybbe Analytics - Comparativo', layout="wide")
    render_comparativo()

st.write("---")

col1, col2 = st.columns([1, 4])

with col1:
    try:
        rodape_image = Image.open('habbla_rodape.jpg')
        st.image(rodape_image, width=110)
    except FileNotFoundError:
        st.write("Logo rodapé não encontrada.")

with col2:
    st.markdown(
        """
        <div style='font-size: 12px; color: gray;'>
            Desenvolvido pela equipe de dados da <b>Habbla</b> | © 2026 Habbla Marketing<br>
            Versão 1.0.0 | Atualizado em: Janeiro/2026<br>
            <a href="mailto:nil@habbla.ai">nil@habbla.ai</a> |
            <a href="https://vybbe.com.br" target="_blank">Site Institucional</a>
        </div>
        """,
        unsafe_allow_html=True
    )