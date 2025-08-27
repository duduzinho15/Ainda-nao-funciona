# 🚀 Garimpeiro Geek

Sistema completo de recomendações de ofertas para Telegram com validação de conversores de afiliados, agendamento automático, fila de ofertas e controle de qualidade.

## ✨ Funcionalidades

### 🔗 Sistema de Afiliados
- **Validação automática** de conversores para Amazon, Mercado Livre, Shopee, Magazine Luiza, AliExpress, Awin e Rakuten
- **Cache inteligente** com Redis para otimizar conversões
- **Validação de URLs** com regex patterns específicos por plataforma
- **Geração de shortlinks** otimizados para cada plataforma

### 📱 Bot do Telegram
- **Formatação dinâmica** de mensagens com templates específicos por plataforma
- **Emojis contextuais** baseados no tipo de oferta e qualidade
- **Sistema de notificações** configurável
- **Templates personalizados** para cada plataforma de afiliados

### ⏰ Agendador Cron
- **Tarefas automáticas** para coleta de ofertas
- **Enriquecimento de preços** em background
- **Postagem automática** na fila
- **Agregação de preços** para análise

### 📋 Sistema de Fila
- **Fila prioritária** de ofertas
- **Sistema de moderação** manual e automática
- **Controle de qualidade** com scoring automático
- **Processamento assíncrono** de ofertas

### 📊 Monitoramento e Métricas
- **Dashboard de conversões** em tempo real
- **Métricas de performance** por plataforma
- **Sistema de alertas** para falhas
- **Motor de otimização** automático

### 🚀 Produção e Escalabilidade
- **Configuração Redis** otimizada para produção
- **Cache distribuído** com fallback em memória
- **Rate limiting** inteligente
- **Sistema de deduplicação** de ofertas

## 🏗️ Arquitetura

```
src/
├── affiliate/          # Conversores de afiliados
│   ├── amazon.py      # Conversor Amazon
│   ├── mercadolivre.py # Conversor Mercado Livre
│   ├── shopee.py      # Conversor Shopee
│   ├── magazineluiza.py # Conversor Magazine Luiza
│   ├── aliexpress.py  # Conversor AliExpress
│   ├── awin.py        # Conversor Awin
│   └── rakuten.py     # Conversor Rakuten
├── app/
│   ├── queue/         # Sistema de fila de ofertas
│   │   ├── offer_queue.py      # Fila principal
│   │   ├── moderation_system.py # Sistema de moderação
│   │   ├── quality_controller.py # Controle de qualidade
│   │   └── queue_manager.py    # Gerenciador da fila
│   └── scheduler/     # Agendador cron
│       ├── cron_manager.py     # Gerenciador de cron jobs
│       ├── job_scheduler.py    # Agendador de tarefas
│       └── task_runner.py     # Executor de tarefas
├── core/              # Componentes principais
│   ├── affiliate_validator.py # Validador de afiliados
│   ├── affiliate_cache.py     # Cache de afiliados
│   ├── conversion_metrics.py  # Métricas de conversão
│   ├── failure_alerts.py      # Sistema de alertas
│   └── optimization_engine.py # Motor de otimização
├── dashboard/         # Dashboard de conversões
│   └── conversion_dashboard.py
├── telegram_bot/      # Bot do Telegram
│   ├── message_builder.py     # Construtor de mensagens
│   ├── notification_manager.py # Gerenciador de notificações
│   └── bot.py                 # Bot principal
└── utils/             # Utilitários
    ├── anti_bot.py           # Medidas anti-bot
    ├── affiliate_validator.py # Validador de URLs
    └── url_utils.py          # Utilitários de URL
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.9+
- Redis 5.0+
- Git

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/garimpeiro-geek.git
cd garimpeiro-geek
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 4. Configure o Redis
```bash
cp config/redis.example.conf config/redis.conf
# Edite o arquivo redis.conf conforme necessário
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=sua_senha_aqui

# Afiliados
AFFILIATE_AMAZON_TAG=garimpeirogeek-20
AFFILIATE_MERCADOLIVRE_ID=seu_id_aqui
AFFILIATE_SHOPEE_ID=seu_id_aqui
AFFILIATE_AWIN_ID=seu_id_aqui
AFFILIATE_RAKUTEN_ID=seu_id_aqui
```

### Configuração Redis
O arquivo `config/redis.production.conf` contém configurações otimizadas para produção:
- Persistência configurada
- Configurações de memória otimizadas
- Logging estruturado
- Configurações de segurança

## 🧪 Testes

### Executar todos os testes
```bash
pytest tests/
```

### Testes unitários
```bash
pytest tests/unit/
```

### Testes de integração
```bash
pytest tests/e2e/
```

### Testes específicos
```bash
# Testar sistema de afiliados
pytest tests/unit/test_affiliate_system.py

# Testar sistema de fila
pytest tests/unit/test_queue_system.py

# Testar agendador
pytest tests/unit/test_scheduler.py
```

## 🚀 Execução

### 1. Iniciar o Redis
```bash
redis-server config/redis.conf
```

### 2. Executar o sistema principal
```bash
python -m src.app.main
```

### 3. Executar o bot do Telegram
```bash
python -m src.telegram_bot.bot
```

### 4. Executar o dashboard
```bash
python -m src.dashboard.conversion_dashboard
```

## 📊 Monitoramento

### Dashboard de Conversões
Acesse o dashboard em tempo real para monitorar:
- Taxa de conversão por plataforma
- Performance dos conversores
- Estatísticas de cache
- Alertas de falhas

### Métricas Disponíveis
- **Conversões**: Total, sucesso, falha
- **Performance**: Tempo de resposta, cache hits/misses
- **Qualidade**: Score das ofertas, taxa de aprovação
- **Sistema**: Uso de memória, conexões Redis

## 🔧 Desenvolvimento

### Formatação de Código
```bash
# Formatação com Black
black src/ tests/

# Linting com Ruff
ruff check src/ tests/

# Verificação de tipos com MyPy
mypy src/
```

### Estrutura de Commits
Seguimos o padrão [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Testes
- `chore:` Manutenção

## 📚 Documentação

- [📋 Relatório de Estrutura Final](docs/RELATORIO_ESTRUTURA_FINAL.md)
- [🔧 Especificações Técnicas](docs/ESPECIFICACAO_GARIMPEIRO_GEEK_COM_RAKUTEN.md)
- [🤖 Documentação do Bot](docs/telegram_bot.md)
- [🔗 APIs de Integração](docs/apis_integracao.md)
- [📊 Exemplos de Afiliados](docs/affiliate_examples.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

Para suporte e dúvidas:
- Abra uma [Issue](https://github.com/SEU_USUARIO/garimpeiro-geek/issues)
- Consulte a [documentação](docs/)
- Verifique os [exemplos](tests/)

## 🎯 Roadmap

- [ ] Interface web para moderação
- [ ] Machine Learning para scoring de ofertas
- [ ] Integração com mais plataformas
- [ ] Sistema de notificações push
- [ ] API REST para integrações externas
- [ ] Dashboard mobile responsivo

---

**Desenvolvido com ❤️ para a comunidade de ofertas e promoções**
