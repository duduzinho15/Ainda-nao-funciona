# 🔐 Configuração de GitHub Secrets para CI/CD

## 📋 **Secrets Necessários**

Para que o pipeline de CI/CD funcione corretamente, configure os seguintes secrets no seu repositório:

### **🔑 Como Configurar:**

1. **Vá para seu repositório no GitHub**
2. **Clique em "Settings"**
3. **No menu lateral, clique em "Secrets and variables" → "Actions"**
4. **Clique em "New repository secret"**

### **📝 Secrets Obrigatórios:**

#### **🔒 Credenciais de Teste:**
```
TEST_TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TEST_TELEGRAM_CHAT_ID=-1001234567890
TEST_ADMIN_USER_ID=123456789
```

#### **🔒 Credenciais da Amazon (para testes):**
```
TEST_AMAZON_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
TEST_AMAZON_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
TEST_AMAZON_ASSOCIATE_TAG=garimpeirogee-20
```

#### **🔒 Credenciais da Shopee (para testes):**
```
TEST_SHOPEE_API_KEY=18330800803
TEST_SHOPEE_API_SECRET=IOMXMSUM5KDOLSYKXQERKCU42SNMJERR
```

#### **🔒 Credenciais da AliExpress (para testes):**
```
TEST_ALIEXPRESS_APP_KEY=517956
TEST_ALIEXPRESS_APP_SECRET=okv8nzEGIvWqV0XxONcN9loPNrYwWDsm
```

#### **🔒 Credenciais da AWIN (para testes):**
```
TEST_AWIN_API_TOKEN=f647c7b9-e8de-44a4-80fe-e9572ef35c10
```

### **🚀 Secrets para Deploy:**

#### **🔒 Servidor de Produção:**
```
PROD_HOST=seu-servidor.com
PROD_USER=seu-usuario
PROD_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
```

#### **🔒 Banco de Dados de Produção:**
```
PROD_DB_HOST=localhost
PROD_DB_NAME=ofertas_prod
PROD_DB_USER=ofertas_user
PROD_DB_PASSWORD=sua_senha_segura
```

### **📊 Secrets para Métricas:**

#### **🔒 Prometheus:**
```
METRICS_ENABLED=true
METRICS_PORT=9308
METRICS_AUTH_TOKEN=seu_token_metrics
```

## ⚠️ **IMPORTANTE:**

- **NUNCA** commite estes secrets no código
- Use **valores diferentes** para desenvolvimento e produção
- **Rotacione** as chaves regularmente
- **Monitore** o uso dos secrets

## 🔍 **Verificação:**

Após configurar os secrets, o pipeline deve:
1. ✅ Executar testes com credenciais de teste
2. ✅ Validar segurança do código
3. ✅ Fazer build do pacote
4. ✅ Deploy automático (se configurado)

---

**🎯 Sistema configurado e seguro para CI/CD!**
