import streamlit as st
import pandas as pd
import plotly.express as px
from textblob import TextBlob

st.set_page_config(page_title="Sentimento – Evento 08/02", layout="wide")

# =========================
# Carregamento dos dados
# =========================
comentarios_path = "1.app_skol/Comentarios_consilidado.xlsx"
links_path = "1.app_skol/links_skol.xlsx"

df = pd.read_excel(comentarios_path)
links_df = pd.read_excel(links_path)

# Normaliza coluna de comentário
coment_col = [c for c in df.columns if 'comente' in c.lower()][0]
df['comentario'] = df[coment_col].astype(str)

# =========================
# Análise de sentimento
# =========================
def classificar_sentimento(texto):
    polaridade = TextBlob(texto).sentiment.polarity
    if polaridade > 0.1:
        return 'Positivo'
    elif polaridade < -0.1:
        return 'Negativo'
    else:
        return 'Neutro'

df['sentimento'] = df['comentario'].apply(classificar_sentimento)

sentimento_dist = df['sentimento'].value_counts().reset_index()
sentimento_dist.columns = ['Sentimento', 'Quantidade']

# =========================
# Layout
# =========================
st.title("📊 Análise de Sentimento – Evento 08/02 (Calvin Harris)")
st.subheader("Visão estratégica para o time de marketing – Vybbe")

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total de Comentários", len(df))
col2.metric("% Neutros", f"{(sentimento_dist.query("Sentimento=='Neutro'")['Quantidade'].sum()/len(df))*100:.1f}%")
col3.metric("% Positivos", f"{(sentimento_dist.query("Sentimento=='Positivo'")['Quantidade'].sum()/len(df))*100:.1f}%")

# =========================
# Gráfico de pizza
# =========================
fig_pizza = px.pie(sentimento_dist, values='Quantidade', names='Sentimento',
                   title='Distribuição de Sentimento nas Redes')
st.plotly_chart(fig_pizza, use_container_width=True)

# =========================
# Comentários por sentimento + Análise Qualitativa
# =========================
st.subheader("📌 Análise Qualitativa da Narrativa")
st.markdown("""
A leitura qualitativa avalia **como o público está falando** sobre o evento,
indo além do volume para entender **tom, contexto cultural e intenção**.
""")

tabs = st.tabs(['🟢 Positivos', '🟡 Neutros', '🔴 Negativos'])

for tab, sentimento in zip(tabs, ['Positivo', 'Neutro', 'Negativo']):
    with tab:
        if sentimento == 'Positivo':
            st.info("Comentários que indicam **curiosidade, empolgação ou percepção de grande evento**. Reforçam oportunidade de amplificação e prova social.")
        elif sentimento == 'Neutro':
            st.warning("Comentários predominantemente **reativos** (marcações, perguntas, observações). Representam o maior potencial de conversão narrativa.")
        else:
            st.error("Comentários com **ironia, estranhamento cultural ou rejeição pontual**. Exigem monitoramento para evitar escalada de narrativa negativa.")
        
        subset = df[df['sentimento'] == sentimento]
        st.dataframe(subset[['comentario']].head(50), use_container_width=True)

# =========================
# Links monitorados
# =========================
st.subheader("🔗 Fontes e Links Monitorados")
st.dataframe(links_df)

# =========================
# Conclusão executiva
# =========================
st.subheader("📈 Conclusão Estratégica")
st.markdown("""
- A narrativa predominante é **neutra**, indicando alto alcance e baixa rejeição.
- Existe **curiosidade** combinada com **estranhamento cultural**, mas sem crise instalada.
- O cenário é favorável para **reposicionamento narrativo** e ativação do público neutro.

**Recomendação:** assumir o controle da narrativa destacando pluralidade cultural e valorização do casting Vybbe.
""")
