# Instruções para Configurar o Repositório no GitHub

## 1. Criar o Repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login na sua conta
2. Clique no botão "+" no canto superior direito e selecione "New repository"
3. Configure o repositório:
   - **Repository name**: `garimpeiro-geek`
   - **Description**: Sistema de Recomendações de Ofertas Telegram - Garimpeiro Geek
   - **Visibility**: Public ou Private (sua escolha)
   - **Initialize this repository with**: NÃO marque nenhuma opção
4. Clique em "Create repository"

## 2. Configurar o Repositório Remoto

Após criar o repositório, execute os seguintes comandos no terminal:

```bash
# Verificar o repositório remoto atual
git remote -v

# Se necessário, remover o remoto atual
git remote remove origin

# Adicionar o novo repositório remoto (substitua USERNAME pelo seu nome de usuário)
git remote add origin https://github.com/USERNAME/garimpeiro-geek.git

# Fazer o push da branch main
git push -u origin main
```

## 3. Estrutura do Projeto

O projeto está organizado com a seguinte estrutura:

```
garimpeiro-geek/
├── src/
│   ├── affiliate/          # Conversores de afiliados
│   ├── app/
│   │   ├── queue/         # Sistema de fila de ofertas
│   │   └── scheduler/     # Agendador cron
│   ├── core/              # Componentes principais
│   ├── dashboard/         # Dashboard de conversões
│   ├── telegram_bot/      # Bot do Telegram
│   └── utils/             # Utilitários
├── tests/                 # Testes unitários e e2e
├── config/                # Configurações
├── docs/                  # Documentação
└── scripts/               # Scripts de execução
```

## 4. Funcionalidades Implementadas

- ✅ Validação de conversores de afiliados
- ✅ Formatação de mensagens para Telegram
- ✅ Agendador cron para tarefas automáticas
- ✅ Sistema de fila de ofertas com moderação
- ✅ Controle de qualidade automático
- ✅ Configuração de produção
- ✅ Sistema de monitoramento
- ✅ Motor de otimização
- ✅ Cache distribuído com Redis
- ✅ Sistema de alertas de falhas
- ✅ Dashboard de métricas de conversão

## 5. Próximos Passos

Após configurar o repositório:

1. Configure as variáveis de ambiente (`.env`)
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure o Redis para produção
4. Execute os testes: `pytest tests/`
5. Configure o bot do Telegram
6. Inicie o sistema: `python -m src.app.main`

## 6. Documentação

- `docs/RELATORIO_ESTRUTURA_FINAL.md` - Estrutura completa do sistema
- `docs/ESPECIFICACAO_GARIMPEIRO_GEEK_COM_RAKUTEN.md` - Especificações técnicas
- `docs/telegram_bot.md` - Documentação do bot
- `docs/apis_integracao.md` - APIs de integração
