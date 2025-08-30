# TODO - Garimpeiro Geek

## ✅ Concluído
- [x] Criar estrutura de pastas padrão (src/, apps/, tests/, scripts/, docs/)
- [x] Migrar scrapers da raiz para src/scrapers/(lojas|comunidades)/
- [x] Migrar providers/* para src/affiliate/* (mantendo lógica de conversão)
- [x] Criar/validar src/core/models.py (Offer) e src/core/settings.py (.env)
- [x] Ajustar imports para absolutos (PYTHONPATH=src)
- [x] Garantir que todos os scrapers retornem Offer
- [x] Criar src/affiliate/rakuten.py com builder click.linksynergy.com
- [x] Criar pipeline de enriquecimento externo (price_enrich.py)
- [x] Criar pipeline de agregação diária (price_aggregate.py)
- [x] Corrigir imports relativos nos arquivos existentes
- [x] Executar todos os testes para validar funcionamento

## 🔄 Em Progresso
- [ ] Gerar relatório detalhado da estrutura final

## 📋 Próximos Passos
- [ ] Executar make fmt && make lint && make type
- [ ] Ajustar manualmente imports específicos que não tenham regra
- [ ] Confirmar se o bot roda em modo sandbox antes de publicar
- [ ] Commit de "checkpoint" com reorganização
- [ ] Criar PRs separados para cada Sprint

## 📊 Status dos Testes
- **Total de testes**: 87
- **Passando**: 86 ✅
- **Falhando**: 1 ❌ (teste E2E KaBuM - conexão real)
- **Taxa de sucesso**: 98.9%

## 🎯 Objetivos Alcançados
1. ✅ Estrutura de pastas limpa e imutável
2. ✅ Regras que o Cursor deve sempre seguir
3. ✅ Especificações de scraping e afiliados
4. ✅ Fluxo completo (descoberta → enriquecimento → link afiliado → postagem → métricas)
5. ✅ Orientações de testes e checklists
6. ✅ Especificação do Dashboard Flet para observabilidade

## 📁 Estrutura Final
```
.
├── src/
│   ├── app/                    ✅ Dashboard Flet
│   ├── affiliate/              ✅ Conversores de afiliados
│   ├── scrapers/               ✅ Scrapers organizados
│   │   ├── lojas/             ✅ Lojas (KaBuM, Amazon, etc.)
│   │   └── comunidades/       ✅ Comunidades (Promobit, Pelando)
│   ├── pipelines/              ✅ Pipelines de processamento
│   ├── telegram_bot/           ✅ Bot Telegram
│   ├── core/                   ✅ Modelos e utilitários
│   ├── utils/                  ✅ Utilitários gerais
│   └── db/                     ✅ Bancos de dados
├── apps/                       ✅ Aplicações externas
├── tests/                      ✅ Testes organizados
├── scripts/                    ✅ Scripts de automação
├── docs/                       ✅ Documentação
└── config/                     ✅ Configurações
```
