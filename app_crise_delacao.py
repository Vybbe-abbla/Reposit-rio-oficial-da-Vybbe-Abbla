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

# Sidebar com fontes
st.sidebar.header("📚 FONTES COMPLETAS (37)")
st.sidebar.info("Lista completa disponível no relatório WhatsApp 👇")

# Linha do tempo principal (mantida igual)
st.markdown("⸻")

st.markdown("""
### 🟥 FASE 1 — ORIGEM (ALTO IMPACTO) **[web:36][web:2]**
**📅 15/12/2025 17:53**

**Revista Piauí + Blog do Magno**  
*Reportagem investigativa* | **Alcance:** Elite jornalística

**Conteúdo-chave:**
- **"Cleverson" = Kleryston Pontes Silveira** (Fortaleza/CE)
- **R$2,5M → 2x R$1,25M**: CINQ Capital (BB) + QIX Sicredi
- **Artistas**: Xand Avião, Zé Vaqueiro, Nattan, Mari Fernandez
- **Nattan**: Réveillon 2026 Macapá confirmado
""")

st.markdown("⸻")

st.markdown("""
### 🟧 FASE 2 — AMPLIFICAÇÃO POLÍTICA **[web:21][web:50]**
**📅 12-13/12/2025**

**Brasil 247 + Roma News**  
- **Mensagens Alcolumbre**: "Tamo junto sempre!" + 🙏
- Reunião 20/12/2024 gabinete Alcolumbre
""")

st.markdown("⸻")

st.markdown("""
### 🟨 FASE 3 — REPLICAÇÃO REGIONAL **(14 sites)**
**📅 13-15/12/2025**

| Site | Destaque |
|------|----------|
| **CN7 Ceará** | "Empresário Ceará" |
| **Roma News** | 2x R$1,25M comprovado |
| **Tribunal Internet** | Corrupção Roberto Carlos |
| **Bahia Notícias** | Kleryston + artistas |
""")

st.markdown("⸻")

st.markdown("""
### 🟦 FASE 5 — REDES SOCIAIS **(🚨 CONSOLIDADA)**
**📅 15/12/2025**

**🐦 X (18 menções):**
**📱 Instagram/Facebook:** Ativo
""")

st.markdown("⸻")

# Status atual
st.markdown("""
## 📊 STATUS ATUAL — 15/12/2025 18:06
**Fase 3→5 completa | X consolidado | Monitoramento intensivo**
""")

# BOTÃO DOWNLOAD WHATSAPP - NOVO!
st.markdown("---")
st.markdown("## 📱 **RELATÓRIO PARA WHATSAPP**")

# Função para gerar texto WhatsApp
def gerar_whatsapp_report():
    whatsapp_text = f"""
🔴 *LINHA DO TEMPO — DELAÇÃO BETO LOUCO*
*Cleverson = Kleryston Pontes Silveira* 👇

📊 *MÉTRICAS ATUALIZADAS (15/12 18:06)*
• 117 menções | 37 fontes | 18 posts X
• Fase 5 CONSOLIDADA (redes sociais)

🟥 *FASE 1 - ORIGEM (12/12)*
📄 Piauí + Blog Magno
✅ "Cleverson" = Kleryston (Fortaleza/CE)
💰 R$2,5M → 2x R$1,25M (CINQ BB + QIX Sicredi)
🎤 Artistas: Xand Avião, Zé Vaqueiro, Nattan
⚠️ Nattan 2026 Macapá confirmado

🟧 *FASE 2 - POLÍTICA (12-13/12)*
📰 Brasil 247 + Roma News
💬 Alcolumbre: "Tamo junto sempre!" 🙏
📅 Reunião 20/12/2024 gabinete

🟨 *FASE 3 - REGIONAL (14 sites)*
🇨🇳 CN7 Ceará: "Empresário Ceará"
🌐 Roma News: Pagamentos comprovados
📰 Tribunal Internet: Corrupção RC

🟦 *FASE 5 - REDES 🚨 ATIVA*
🐦 X (18 menções):
@donizetearruda7: "DELAÇÃO R$2,5M"
@ICLNoticias: "Beto Louco x Alcolumbre"

📍 *STATUS: Fase 5 consolidada*
Monitoramento intensivo ativo 🔄

🔗 *FONTES PRINCIPAIS (37):*
Piauí • Brasil247 • CN7 • Bahia Notícias
Roma News • Tribunal Internet • 30+ outras

*Gerado: 15/12/2025 18:06 BRT*
    """
    return whatsapp_text.strip()

# Botão download
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("**📥 Baixe o relatório formatado para WhatsApp**")
with col2:
    # Download TXT
    whatsapp_content = gerar_whatsapp_report()
    st.download_button(
        label="📱 Enviar WhatsApp",
        data=whatsapp_content,
        file_name="Relatorio_Delacao_Beto_Louco_151225.txt",
        mime="text/plain",
        help="Clique para baixar e copiar no WhatsApp"
    )

# Preview do conteúdo
with st.expander("👁️ **Pré-visualizar conteúdo WhatsApp**"):
    st.code(whatsapp_content, language="text")
    st.info("💡 *Cole este texto diretamente no WhatsApp!*")

# Footer
st.markdown("---")
st.caption("🔄 *Monitoramento automatizado | Atualização: 15/12/2025 18:06 BRT*")
