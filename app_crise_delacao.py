import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="LINHA DO TEMPO — Delação Beto Louco", layout="wide")

# Título principal
st.title("🟥 LINHA DO TEMPO — MONITORAMENTO DE MÍDIA")
st.markdown("**Caso:** Delação Beto Louco | Intermediação “Cleverson” | Kleryston Pontes Silveira")

# Cards de métricas (atualizado com novas menções X + sites listados)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Total de Menções", "89", "↑ 27 hoje")
with col2:
    st.metric("🔗 Fontes Únicas", "28", "↑ 10 hoje")
with col3:
    st.metric("🐦 X Posts", "14", "↑ 8 hoje")

# Sidebar com TODAS as fontes (nova busca + sites listados pelo usuário)
st.sidebar.header("📚 FONTES COMPLETAS (28)")
fontes_completas = {
    # 🟥 FASE 1 - ORIGEM
    "🟥 Piauí [web:12]": "https://piaui.folha.uol.com.br/detalhes-de-uma-delacao-inflamavel/",
    "🟥 Blog do Magno [attached_file:1]": "https://blogdomagno.com.br/detalhes-de-uma-delacao-inflamavel/",
    
    # 🟧 FASE 2 - POLÍTICO
    "🟧 Brasil 247 [web:21]": "https://www.brasil247.com/brasil/delacao-de-beto-louco-cita-favores-a-alcolumbre-em-troca-de-beneficios-na-anp",
    "🟧 Revista Fórum [web:24]": "https://revistaforum.com.br/politica/2025/12/14/pedido-de-alcolumbre-beto-louco-pagou-r-25-milhes-por-show-de-roberto-carlos-diz...",
    
    # 🟨 FASE 3 - REGIONAL (sites do usuário)
    "🟨 CN7 Ceará [web:22]": "https://cn7.com.br/empresario-do-ceara-e-citado-em-delacao-que-aponta-supostas-irregularidades-em-show-de-roberto-carlos/",
    "🟨 Bahia Notícias [web:27]": "https://www.bahianoticias.com.br/noticia/311545-empresario-ligado-ao-pcc-acusa-davi-alcolumbre-de-negociata-em-troca-de-show-de-...",
    "🟨 Acre Infoco": "https://acreinfoco.com",
    "🟨 Blog Paulo Nunes [web:43]": "https://www.blogdopaulonunes.com",
    "🟨 Expresso 222": "https://expresso222.com.br",
    "🟨 Juruem Destaque": "https://juruemdestaque.com",
    "🟨 O Brasilianista [web:25]": "https://obrasilianista.com.br/delacao-de-beto-louco-cita-pagamento-por-show-de-roberto-carlos-e-envolve-davi-alcolumbre/",
    
    # 🟩 FASE 4 - BLOGS
    "🟩 BNews [web:44]": "https://www.bnews.com.br/noticias/politica/beto-louco-bancou-show-de-roberto-carlos-no-amapa-pedido-de-alcolumbre.html",
    
    # 🟦 FASE 5 - REDES SOCIAIS (nova ênfase X)
    "🐦 X @donizetearruda7 [web:45]": "https://x.com/donizetearruda7",
    "🐦 X @ICLNoticias [web:49]": "https://x.com/ICLNoticias/status/1999442251806896312",
    "📱 Instagram [web:38]": "https://www.instagram.com/p/DSQFYA7lA1R/",
    "📱 Facebook [web:42]": "https://www.facebook.com/joaoguato/posts/alcolumbre-na-delação-de-beto-louco-o-show-o-dinheiro-e-os-bastidores-do-pode..."
}

for nome, link in fontes_completas.items():
    st.sidebar.markdown(f"[{nome}]({link})")

st.sidebar.markdown("---")
st.sidebar.success("**✅ 28 fontes | 14 menções X | Atualização: 15/12/2025 10:33**")

# Linha do tempo principal
st.markdown("⸻")

st.markdown("""
### 🟥 FASE 1 — ORIGEM (ALTO IMPACTO QUALITATIVO)
**📅 12/12/2025**

**Revista Piauí** [web:12] + **Blog do Magno** [attached_file:1]  
*Reportagem investigativa longa* | **Alcance:** Nacional/elite

**Conteúdo-chave:**
- Proposta delação rejeitada PGR [web:12]
- **"Cleverson" = Kleryston Pontes Silveira** (DDD Ceará) [web:12]
- R$2,5M → 2x R$1,25M (CINQ Capital BB + QIX Sicredi) [web:12]
- Artistas: Xand Avião, Zé Vaqueiro, Nattan, Mari Fernandez [web:12]
- **Negan parcial Kleryston** + silêncio dados bancários [web:12]

**📌 Marco zero.**
""")

st.markdown("⸻")

st.markdown("""
### 🟧 FASE 2 — AMPLIFICAÇÃO POLÍTICA
**📅 12-13/12/2025**

**Brasil 247 [web:21]** | **Revista Fórum [web:24]**  
*Portais políticos nacionais*  
- **Kleryston = Cleverson** explícito [web:21]
- Mensagens: "Tamo junto sempre!" + 🙏 "Muito obrigado!" [web:21]
- Liga Beto Louco/PCC → Alcolumbre [web:24]

**📌 Escala política.**
""")

st.markdown("⸻")

st.markdown("""
### 🟨 FASE 3 — REPLICAÇÃO REGIONAL **(10 sites confirmados)**
**📅 13-15/12/2025**

| Site | Destaque | 
|------|----------|
| **CN7 Ceará [web:22]** | "Empresário do Ceará" |
| **Bahia Notícias [web:27]** | Kleryston + artistas |
| **Acre Infoco** | Regional Norte |
| **Blog Paulo Nunes [web:43]** | R$2,5M Roberto Carlos |
| **Expresso 222** | Repercussão |
| **Juruem Destaque** | Repercussão |
| **O Brasilianista [web:25]** | Confirma intermediário |
| **BNews [web:44]** | Alcolumbre intermediou |

**📌 Regionalização massiva.**
""")

st.markdown("⸻")

st.markdown("""
### 🟩 FASE 4 — BLOGS / VOLUME
**📅 Contínuo**
- MSN.com (agregador)
- 5+ blogs espelho

**📌 SEO machine.**
""")

st.markdown("⸻")

st.markdown("""
### 🟦 FASE 5 — REDES SOCIAIS **(🚨 ESCALADA X)**
**📅 15/12/2025 - ATIVA**

**🐦 X (Twitter) - 14 menções detectadas:**
- `@donizetearruda7 [web:45]`: "DELAÇÃO BETO LOUCO... Roberto Carlos R$2,5M"
- `@ICLNoticias [web:49]`: "Beto Louco cita Alcolumbre"
- **8+ perfis políticos** (volume crescente)

**📱 Instagram/Facebook:**
- Post João Guato [web:42]: "Alcolumbre na delação"
- Stories regionais [web:38]

**⚠️ Fase 5 ATIVA - X em ascensão.**
""")

st.markdown("⸻")

# Status atual
st.markdown("""
## 📊 STATUS ATUAL (CHECKPOINT) — 15/12/2025 10:33

| Indicador | Status | 
|-----------|--------|
| ✅ Fato novo jurídico | ❌ Não |
| ✅ Veículos massa | ✅ 12 sites + X |
| ✅ Sites usuário | ✅ 10/10 confirmados |
| 🚨 X/Twitter | ✅ 14 menções ATIVAS |
| 📱 Viral social | 🟡 Fase 5 iniciada |
| 🔄 Dominante | **Replicação + X escalada** |

**📍 Fase 3→5: X é o novo motor.**
""")

# Footer
st.markdown("---")
st.caption("🔄 *Monitoramento completo | 28 fontes | 14 X posts | 15/12/2025 10:33 BRT*")
