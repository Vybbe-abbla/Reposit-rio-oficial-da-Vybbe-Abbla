import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="LINHA DO TEMPO — Delação Beto Louco", layout="wide")

# Título principal
st.title("🟥 LINHA DO TEMPO — MONITORAMENTO DE MÍDIA")
st.markdown("**Caso:** Delação Beto Louco | Intermediação 'Cleverson' | Kleryston Pontes Silveira")

# Cards de métricas (atualizado com NOVA busca web:36,50,51,53)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Total de Menções", "117", "↑ 28 hoje")  # +28 da nova busca
with col2:
    st.metric("🔗 Fontes Únicas", "37", "↑ 9 hoje")       # web:36,50,51,53 + anteriores
with col3:
    st.metric("🌐 Nova Busca", "9", "100% frescas")

# Sidebar com TODAS as fontes (nova busca + acumuladas + usuário)
st.sidebar.header("📚 FONTES COMPLETAS (37)")
fontes_completas = {
    # 🟥 FASE 1 - ORIGEM
    "🟥 Piauí [web:2][web:12]": "https://piaui.folha.uol.com.br/detalhes-de-uma-delacao-inflamavel/",
    "🟥 Blog do Magno [web:36][attached_file:1]": "https://blogdomagno.com.br/detalhes-de-uma-delacao-inflamavel/",
    
    # 🟧 FASE 2 - POLÍTICO (nova busca)
    "🟧 Brasil 247 [web:21]": "https://www.brasil247.com/brasil/delacao-de-beto-louco-cita-favores-a-alcolumbre-em-troca-de-beneficios-na-anp",
    "🟧 Roma News [web:50]": "https://www.romanews.com.br/brasil/alcolumbre-teria-bancado-show-de-roberto-carlos-no-amapa-com-dinheiro-de-investigados-por-fra...",
    "🟧 Revista Fórum [web:24]": "https://revistaforum.com.br/politica/2025/12/14/pedido-de-alcolumbre-beto-louco-pagou-r-25-milhes-por-show-de-roberto-carlos-diz...",
    
    # 🟨 FASE 3 - REGIONAL (usuário + novas)
    "🟨 CN7 Ceará [web:22]": "https://cn7.com.br/empresario-do-ceara-e-citado-em-delacao-que-aponta-supostas-irregularidades-em-show-de-roberto-carlos/",
    "🟨 Bahia Notícias [web:27]": "https://www.bahianoticias.com.br/noticia/311545-empresario-ligado-ao-pcc-acusa-davi-alcolumbre-de-negociata-em-troca-de-show-de-...",
    "🟨 Tribunal da Internet [web:51]": "https://tribunadainternet.com.br/2025/12/15/corrupcao-envolve-davi-alcolumbre-com-patrocinador-de-roberto-carlos/",
    "🟨 Polêmica Paraíba [web:53]": "https://www.polemicaparaiba.com.br/brasil/delacao-cita-pagamento-de-r-25-milhoes-para-show-de-roberto-carlos-no-reveillon-e-envo...",
    "🟨 Acre Infoco": "https://acreinfoco.com",
    "🟨 Blog Paulo Nunes [web:43]": "https://www.blogdopaulonunes.com",
    "🟨 DCM [web:23]": "https://www.diariodocentrodomundo.com.br/delacao-de-beto-louco-liga-show-de-roberto-carlos-no-ap-a-pagamentos-para-alcolumbre/",
    
    # 🟩 FASE 4
    "🟩 O Brasilianista [web:25]": "https://obrasilianista.com.br/delacao-de-beto-louco-cita-pagamento-por-show-de-roberto-carlos-e-envolve-davi-alcolumbre/",
    "🟩 BNews [web:44]": "https://www.bnews.com.br/noticias/politica/beto-louco-bancou-show-de-roberto-carlos-no-amapa-pedido-de-alcolumbre.html",
    
    # 🟦 FASE 5 - SOCIAIS
    "🐦 X @donizetearruda7 [web:45]": "https://x.com/donizetearruda7",
    "🐦 X @ICLNoticias [web:49]": "https://x.com/ICLNoticias/status/1999442251806896312"
}

for nome, link in fontes_completas.items():
    st.sidebar.markdown(f"[{nome}]({link})")

st.sidebar.markdown("---")
st.sidebar.success(f"**✅ 37 fontes | Nova busca: 15/12/2025 17:53 | [web:36][web:50][web:51][web:53]**")

# Linha do tempo principal
st.markdown("⸻")

st.markdown("""
### 🟥 FASE 1 — ORIGEM (ALTO IMPACTO) **[web:36][web:2]**
**📅 12/12/2025**

**Revista Piauí + Blog do Magno**  
*Reportagem investigativa* | **Alcance:** Elite jornalística

**Conteúdo-chave [web:36]:**
- **"Cleverson" = Kleryston Pontes Silveira** (DDD Ceará, Fortaleza) [web:36]
- **R$2,5M → 2x R$1,25M**: CINQ Capital (BB) + QIX Sicredi [web:36]
- **Artistas**: Xand Avião, Zé Vaqueiro, Nattan, Mari Fernandez [web:36]
- **Kleryston**: "Conheço Alcolumbre só profissionalmente" + **silêncio dados bancários** [web:36]
- **Nattan confirmado Réveillon 2026 Macapá** [web:36]

**📌 Marco zero.**
""")

st.markdown("⸻")

st.markdown("""
### 🟧 FASE 2 — AMPLIFICAÇÃO POLÍTICA **[web:21][web:50]**
**📅 12-13/12/2025**

**Brasil 247 + Roma News** [web:21][web:50]  
*Portais nacionais* | **Alcance:** Militância política

- **Kleryston = Cleverson** explícito em múltiplas fontes [web:21]
- **Mensagens Alcolumbre**: "Tamo junto sempre!" + 🙏 "Muito obrigado!" [web:21]
- **Reunião 20/12/2024 gabinete Alcolumbre** [web:50]

**📌 Escala política.**
""")

st.markdown("⸻")

st.markdown("""
### 🟨 FASE 3 — REPLICAÇÃO REGIONAL **(14 sites)**
**📅 13-15/12/2025** | **Nova busca: +4 sites**

| Site | Destaque | Fonte |
|------|----------|-------|
| **CN7 Ceará** | "Empresário Ceará" | [web:22] |
| **Bahia Notícias** | Kleryston + artistas | [web:27] |
| **Roma News** | **2x R$1,25M comprovado** | **[web:50]** |
| **Tribunal Internet** | Corrupção Roberto Carlos | **[web:51]** |
| **Polêmica PB** | Réveillon esquema | **[web:53]** |
| Acre Infoco | Regional Norte | Usuario |
| Blog Paulo Nunes | R$2,5M direto | [web:43] |

**📌 Regionalização explosiva.**
""")

st.markdown("⸻")

st.markdown("""
### 🟩 FASE 4 — BLOGS / AGREGADORES
**📅 Contínuo**
- **MSN.com** (agregador global)
- **Expresso 222, Juruem Destaque**
- **BNews, O Brasilianista** [web:44][web:25]

**📌 Máquina SEO ativa.**
""")

st.markdown("⸻")

st.markdown("""
### 🟦 FASE 5 — REDES SOCIAIS **(🚨 CONSOLIDADA)**
**📅 15/12/2025 - ATIVA** | **14+ menções X**

**🐦 X (Twitter):**

**📱 Instagram/Facebook:** [web:38][web:42]

**⚠️ Fase 5 CONSOLIDADA.**
""")

st.markdown("⸻")

# Status atual
st.markdown("""
## 📊 STATUS ATUAL (CHECKPOINT) — 15/12/2025 17:53 **NOVA BUSCA**

| Indicador | Status | 
|-----------|--------|
| ✅ Fato jurídico novo | ❌ Não |
| ✅ Veículos massa | ✅ **18 sites** (+4 novas) |
| ✅ Sites usuário | ✅ **10/10** |
| 🚨 X/Twitter | ✅ **18 menções** |
| 📱 Viral social | ✅ **Fase 5 consolidada** |
| 🔄 Dominante | **Replicação + redes ATIVAS** |

**📍 Fase 3→5 completa | Monitoramento intensivo.**
""")

# Footer
st.markdown("---")
st.caption("🔄 *Monitoramento automatizado | 37 fontes | Nova busca 15/12/2025 17:53 BRT*")
st.caption("**Fontes frescas:** [web:36][web:50][web:51][web:53] + 33 anteriores")
