# Garimpeiro Geek — Especificação Funcional & Técnica

Este documento descreve **todas as regras, arquitetura e funcionamento** do projeto de recomendação de ofertas via Telegram.

---
## 📌 Objetivo
Organizar de forma definitiva o projeto **Garimpeiro Geek**, garantindo:
- Estrutura de pastas limpa e imutável
- Regras que o Cursor deve sempre seguir
- Especificações de scraping e afiliados
- Fluxo completo (descoberta → enriquecimento → link afiliado → postagem → métricas)
- Orientações de testes e checklists
- Especificação do Dashboard Flet para observabilidade

---
## 📂 Estrutura de pastas
```
.
├── src/
│   ├── app/
│   ├── affiliate/
│   ├── scrapers/
│   │   ├── lojas/
│   │   └── comunidades/
│   ├── posting/
│   ├── telegram_bot/
│   ├── core/
│   ├── utils/
│   └── db/
├── apps/
│   └── flet_dashboard/
├── tests/
├── scripts/
├── docs/
├── .env.example
├── pyproject.toml
├── Makefile
└── README.md
```

---
## ⚙️ Regras para o Cursor
1. Nunca criar arquivos fora da árvore definida acima.
2. Scrapers de lojas → `src/scrapers/lojas/`  
   Scrapers de comunidades → `src/scrapers/comunidades/`  
   Conversores de afiliados → `src/affiliate/`
3. Sempre usar **type hints** e **docstrings** claras.
4. Nunca commitar credenciais — usar `.env`.
5. Todos os scrapers devem produzir objeto `Offer` com campos:  
   `title, price, price_before, store, url, images, available, extra`

---
## 🔗 Afiliações
- **Awin**: Comfy, Trocafy, LG, Kabum, Ninja, Samsung  
- **Shopee**: shortlink `s.shopee.com.br/...`  
- **AliExpress**: shortlink `s.click.aliexpress.com/e/...`  
- **Mercado Livre**: shortlink `mercadolivre.com/sec/...` (etiqueta `garimpeirogeek`)  
- **Magazine Luiza**: link da vitrine `magazinegarimpeirogeek`  
- **Amazon**: normalização com `tag=garimpeirogee-20`
- **Rakuten Advertising**: Hype Games (MID 53304, Group offer ID: 1799190), Nuuvem (MID 46796, Group offer ID: 1692636)

(Detalhes de exemplos de links estão nos arquivos auxiliares em `docs/`)  

---
## 🛠️ Fluxo de Oferta
1. Descoberta → scraping de comunidades (Promobit, Pelando, MeuPC.net)
2. Enriquecimento → scraping da loja (título, preço, estoque, imagens)
3. Conversão de link → conforme plataforma (Awin, ML, Magalu, Amazon, Shopee, AliExpress)
4. Deduplicação → evitar repostagens
5. Template de mensagem → formatação por loja e tipo de oferta
6. Publicação no Telegram
7. Registro em métricas (analytics.sqlite)

---
## ✅ Testes e Checklists
- **Unitários**: geração de deeplink Awin, normalização Amazon, contrato Offer
- **Smoke**: pipeline mínimo até publicação em canal de testes
- **E2E**: scraping real + conversão + template + postagem em sandbox

Checklist PR:
- [ ] Código formatado (`make fmt`)
- [ ] Lint/ruff sem erros
- [ ] Tipagem (mypy) OK
- [ ] Testes passando
- [ ] Nenhum arquivo fora da árvore oficial
- [ ] Nenhuma credencial em commit

---
## 📊 Dashboard Flet (Especificação)
- **Objetivo**: Monitorar receita, performance e controlar o bot
- **Seções**:
  - Header (nome e status)
  - KPIs (Receita Hoje, 7d, 30d)
  - Controles (Iniciar/Parar bot, status atual)
  - Toggles de plataformas (Awin, ML, Magalu, Amazon, Shopee, AliExpress)
  - Receita por plataforma (gráfico/barras)
  - Performance de scrapers (latência, sucesso/erro)
- **Estilo**: Flat, minimalista, moderno, paleta contida, tipografia clara, micro animações
- **Dados**: banco `analytics.sqlite` com tabelas `revenue` e `perf`

---
## 📅 Roadmap
1. Scrapers Awin + Deeplink + API
2. Mercado Livre (shortlink + cache)
3. Amazon (normalização + scraping robusto)
4. Shopee (API, shortlink + cache)
5. Magazine Luiza (vitrine)
6. AliExpress (API, shortlink)
7. Rakuten Advertising API	
8. Dashboard Flet + Observabilidade completa

---
## 📌 Onde salvar este documento
Coloque este arquivo em:
```
docs/ESPECIFICACAO_GARIMPEIRO_GEEK.md
```
E adicione no README.md um link: **“Guia do Projeto + Regras do Cursor”**

---
## 📖 Apêndice (referências)
- Arquivos: `Regras de alguma afiliações na Awin.txt`, `Informações base de geração de link.txt`【113†source】【114†source】
- Etiqueta Mercado Livre: `garimpeirogeek`
- Amazon tag: `garimpeirogee-20`
