# Guia de Configuração da API da Shopee

## 🚀 Configuração Rápida

### 1. Criar Arquivo de Configuração

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# API da Shopee
SHOPEE_API_KEY=sua_api_key_aqui
SHOPEE_API_SECRET=sua_api_secret_aqui
SHOPEE_PARTNER_ID=seu_partner_id_aqui
SHOPEE_SHOP_ID=seu_shop_id_aqui  # Opcional
```

### 2. Obter Credenciais da API

#### Passo 1: Acessar Portal de Parceiros
- Vá para: [https://partner.shopeemobile.com](https://partner.shopeemobile.com)
- Faça login ou crie uma conta de parceiro

#### Passo 2: Solicitar Acesso à API
- No painel de parceiros, procure por "API Access" ou "Developer Tools"
- Solicite acesso à API de produtos
- Aguarde aprovação (geralmente 1-3 dias úteis)

#### Passo 3: Obter Credenciais
Após aprovação, você receberá:
- **API Key**: Chave de identificação
- **API Secret**: Segredo para assinatura
- **Partner ID**: ID único do seu parceiro
- **Shop ID**: ID da sua loja (se aplicável)

### 3. Testar Configuração

Execute o script de teste para verificar se tudo está funcionando:

```bash
python test_shopee_api.py
```

## 🔧 Configuração Detalhada

### Variáveis de Ambiente

| Variável | Descrição | Obrigatória | Exemplo |
|----------|-----------|-------------|---------|
| `SHOPEE_API_KEY` | Chave da API fornecida pela Shopee | ✅ | `sk_1234567890abcdef` |
| `SHOPEE_API_SECRET` | Segredo para gerar assinaturas | ✅ | `secret_abcdef123456` |
| `SHOPEE_PARTNER_ID` | ID único do seu parceiro | ✅ | `12345` |
| `SHOPEE_SHOP_ID` | ID da sua loja (se aplicável) | ❌ | `67890` |

### Estrutura do Arquivo .env

```bash
# ========================================
# CONFIGURAÇÕES DO BOT TELEGRAM
# ========================================
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
ADMIN_USER_ID=seu_user_id_aqui

# ========================================
# CONFIGURAÇÕES DA AMAZON PA-API
# ========================================
AMAZON_ACCESS_KEY=sua_access_key_aqui
AMAZON_SECRET_KEY=sua_secret_key_aqui
AMAZON_ASSOCIATE_TAG=seu_associate_tag_aqui
AMAZON_REGION=us-east-1

# ========================================
# CONFIGURAÇÕES DA API DA SHOPEE
# ========================================
SHOPEE_API_KEY=sua_shopee_api_key_aqui
SHOPEE_API_SECRET=sua_shopee_api_secret_aqui
SHOPEE_PARTNER_ID=seu_partner_id_aqui
SHOPEE_SHOP_ID=seu_shop_id_aqui

# ========================================
# CONFIGURAÇÕES DA API DA AWIN
# ========================================
AWIN_API_TOKEN=seu_awin_token_aqui
AWIN_PUBLISHER_ID=seu_publisher_id_aqui

# ========================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# ========================================
DB_NAME=ofertas.db
```

## 🧪 Validação da Configuração

### 1. Verificar Importação
```bash
python -c "from shopee_api_integration import ShopeeAPIIntegration; print('✅ Importação OK')"
```

### 2. Verificar Inicialização
```bash
python -c "from shopee_api_integration import ShopeeAPIIntegration; api = ShopeeAPIIntegration(); print(f'API Disponível: {api.api_available}')"
```

### 3. Teste Completo
```bash
python test_shopee_api.py
```

## 🚨 Solução de Problemas

### Erro: "API da Shopee não configurada"

**Causa**: Variáveis de ambiente não encontradas ou vazias.

**Solução**:
1. Verifique se o arquivo `.env` existe na raiz do projeto
2. Confirme se as variáveis estão preenchidas corretamente
3. Reinicie o terminal/IDE após criar o arquivo `.env`

### Erro: "Falha na conexão com a API da Shopee"

**Causa**: Credenciais inválidas ou API não aprovada.

**Solução**:
1. Verifique se as credenciais estão corretas
2. Confirme se o acesso à API foi aprovado
3. Aguarde 24-48h após aprovação para ativação

### Erro: "Rate limit exceeded"

**Causa**: Muitas requisições em pouco tempo.

**Solução**:
1. Aguarde alguns minutos antes de fazer novas requisições
2. Reduza o número de produtos buscados por vez
3. Implemente delays maiores entre requisições

## 📊 Monitoramento

### Logs Importantes

Após a configuração, monitore estes logs:

```
✅ API da Shopee configurada e ativada!
✅ Conexão com a API da Shopee estabelecida com sucesso!
✅ Encontradas X ofertas na Shopee
```

### Métricas de Sucesso

- **Taxa de sucesso**: >95% das requisições
- **Tempo de resposta**: <5 segundos
- **Ofertas encontradas**: >10 por busca

## 🔄 Atualizações

### Verificar Versão da API
A integração usa a versão v2 da API da Shopee. Para atualizações:

1. Consulte a [documentação oficial da Shopee](https://open.shopee.com)
2. Atualize o arquivo `shopee_api_integration.py` se necessário
3. Execute os testes após atualizações

### Manutenção
- Verifique as credenciais mensalmente
- Monitore os logs de erro
- Atualize as dependências conforme necessário

## 📞 Suporte

### Recursos de Ajuda
1. **Documentação da API**: [https://open.shopee.com](https://open.shopee.com)
2. **Portal de Parceiros**: [https://partner.shopeemobile.com](https://partner.shopeemobile.com)
3. **Testes Locais**: `python test_shopee_api.py`
4. **Logs do Sistema**: Verifique a pasta `logs/`

### Contato
Para suporte técnico específico da integração:
- Execute os testes e verifique os logs
- Consulte a documentação da API da Shopee
- Verifique as configurações no arquivo `.env`

---

## ✅ Checklist de Configuração

- [ ] Criado arquivo `.env` na raiz do projeto
- [ ] Preenchidas todas as variáveis obrigatórias da Shopee
- [ ] Credenciais da API obtidas e aprovadas
- [ ] Teste de importação executado com sucesso
- [ ] Teste de inicialização executado com sucesso
- [ ] Teste de conexão executado com sucesso
- [ ] Todos os testes passando (`python test_shopee_api.py`)
- [ ] Bot principal testado com a nova integração

**Status**: 🟡 Aguardando configuração das credenciais
