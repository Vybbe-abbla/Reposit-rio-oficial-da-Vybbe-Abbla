import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuração da página
st.set_page_config(page_title="LINHA DO TEMPO — Delação Beto Louco", layout="wide")

# Título principal
st.title("🟥 LINHA DO TEMPO — MONITORAMENTO DE MÍDIA")
st.markdown("**Caso:** Delação Beto Louco | Intermediação 'Cleverson' | Kleryston Pontes Silveira")

# Cards de métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Total de Menções", "117", "↑ 28 hoje")
with col2:
    st.metric("🔗 Fontes Únicas", "37", "↑ 9 hoje")
with col3:
    st.metric("🌐 Nova Busca", "9", "100% frescas")

# SIDEBAR CORRIGIDO COM DESTAQUE DAS NOVAS FONTES DE HOJE 🔥
st.sidebar.header("📚 **FONTES COMPLETAS (37)**")

# 🔥 DESTAQUE - NOVAS FONTES DE HOJE (15/12) - CORRIGIDO
st.sidebar.markdown("---")
st.sidebar.markdown("🔥 **NOVAS HOJE (15/12) - 17:53**")
st.sidebar.error("🚨 [web:50][web:51][web:53] NOVAS FORTES!")

novas_fontes = {
    "🚨 **Roma News** [web:50]": "https://www.romanews.com.br/brasil/alcolumbre-teria-bancado-show-de-roberto-carlos-no-amapa-com-dinheiro-de-investigados-por-fra...",
    "🚨 **Tribunal Internet** [web:51]": "https://tribunadainternet.com.br/2025/12/15/corrupcao-envolve-davi-alcolumbre-com-patrocinador-de-roberto-carlos/",
    "🚨 **Polêmica PB** [web:53]": "https://www.polemicaparaiba.com.br/brasil/delacao-cita-pagamento-de-r-25-milhoes-para-show-de-roberto-carlos-no-reveillon-e-envo...",
    "🟥 **Blog Magno** [web:36]": "https://blogdomagno.com.br/detalhes-de-uma-delacao-inflamavel/"
}

for nome, link in novas_fontes.items():
    st.sidebar.markdown(f"**{nome}**")
    st.sidebar.markdown(f"[🔗 Acessar]({link})")

# 📋 DEMAIS FONTES
st.sidebar.markdown("---")
st.sidebar.markdown("📋 **Demais Fontes (33)**")
st.sidebar.info("Piauí • Brasil247 • CN7 • Bahia Notícias • X posts • 28 outras")

# Linha do tempo principal (resumida)
st.markdown("⸻")
st.markdown("""
### 🟥 FASE 1 — ORIGEM
**Piauí [web:2]**: "Cleverson" = **Kleryston Pontes Silveira**
💰 R$2,5M (2x R$1,25M) | 🎤 Xand Avião, Nattan, Zé Vaqueiro
""")

st.markdown("⸻")
st.markdown("""
### 🟧 FASE 2 — POLÍTICA
**Brasil 247 [web:21]**: "Tamo junto sempre!" 🙏 Alcolumbre
**Roma News [web:50]**: Reunião 20/12 gabinete
""")

st.markdown("⸻")
st.markdown("""
### 🟨 FASE 3 — REGIONAL (🚨 +4 HOJE)
| Site | Status |
|------|--------|
| **Roma News** | 🔥 NOVA |
| **Tribunal Internet** | 🔥 NOVA |
| **Polêmica PB** | 🔥 NOVA |
| CN7 Ceará | Confirmada |
""")

st.markdown("⸻")
st.markdown("""
### 🟦 FASE 5 — X CONSOLIDADA
🐦 **18 menções X** | @donizetearruda7, @ICLNoticias
""")

# Status atual
st.markdown("## 📊 STATUS — 15/12/2025 18:26")
st.success("**🚨 4 NOVAS FONTES HOJE** | Fase 5 ativa | 117 menções")

# BOTÃO WHATSAPP
st.markdown("---")
st.markdown("## 📱 **RELATÓRIO WHATSAPP**")

def gerar_whatsapp_report():
    return f"""
🔴 *LINHA DO TEMPO DELAÇÃO BETO LOUCO*
*Cleverson = Kleryston Pontes Silveira*

📊 *15/12 18:26* | 117 menções | 37 fontes
🔥 *4 NOVAS HOJE*: Roma News, Tribunal Internet, Polêmica PB

🟥 *ORIGEM*: Piauí → Kleryston (Fortaleza/CE)
💰 R$2,5M → CINQ BB + QIX Sicredi
🎤 Xand Avião, Nattan (2026 Macapá)

🟦 *X ATIVO*: 18 menções | @donizetearruda7

📍 *Fase 5 CONSOLIDADA*
*Gerado: 15/12/2025 18:26*
"""

whatsapp_content = gerar_whatsapp_report()
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("**📥 Baixe relatório formatado**")
with col2:
    st.download_button(
        label="📱 WhatsApp",
        data=whatsapp_content,
        file_name="Delacao_Beto_Louco_151225_1826.txt",
        mime="text/plain"
    )

with st.expander("👁️ Preview WhatsApp"):
    st.code(whatsapp_content, language="text")

# Footer
st.markdown("---")
st.caption("🔄 *Atualização: 15/12/2025 18:26 BRT | 4 novas fontes destacadas*")
