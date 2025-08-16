# 🚀 GUIA COMPLETO: API DA SHOPEE - TRATAMENTO DO ERRO 10035

## 🎯 Objetivo

Este guia explica como usar a **API melhorada da Shopee** para capturar e analisar o **erro 10035**, que é solicitado pela equipe de suporte da Shopee para debug.

## 📁 Arquivos Criados

### 1. **`shopee_api_enhanced.py`** - API Principal Melhorada
- ✅ Tratamento específico para erro 10035
- ✅ Sistema de retry automático
- ✅ Logs detalhados para debug
- ✅ Tratamento de rate limiting
- ✅ Headers otimizados

### 2. **`test_shopee_error_10035.py`** - Script de Teste Específico
- ✅ Testes automatizados para capturar erro 10035
- ✅ Logs detalhados em arquivo
- ✅ Salvamento de respostas e erros
- ✅ Análise automática de erros

## 🔧 Como Usar

### Passo 1: Instalar Dependências
```bash
pip install requests urllib3
```

### Passo 2: Executar o Script de Teste
```bash
python test_shopee_error_10035.py
```

### Passo 3: Fornecer Credenciais
- **App ID**: Seu ID de aplicação da Shopee
- **App Secret**: Sua chave secreta da Shopee

## 📊 O que o Script Faz

### 1. **Teste de Conexão Básica**
- Verifica se a API está acessível
- Testa autenticação básica

### 2. **Busca de Ofertas**
- Tenta buscar ofertas de produtos
- Usa query GraphQL otimizada

### 3. **Busca por Palavra-chave**
- Testa busca por "smartphone"
- Verifica funcionalidade de busca

### 4. **Query de Schema**
- Testa query simples de schema
- Verifica estrutura da API

## 📋 Arquivos de Log Gerados

### 1. **`shopee_error_10035_debug.log`** - Log Principal
- ✅ Todas as requisições e respostas
- ✅ Detalhes de autenticação
- ✅ Timestamps precisos
- ✅ Níveis de log (DEBUG, INFO, WARNING, ERROR)

### 2. **`erro_10035_detalhes.json`** - Detalhes do Erro 10035
- ✅ Captura específica do erro 10035
- ✅ Informações completas do erro
- ✅ Contexto da requisição
- ✅ Timestamp da ocorrência

### 3. **`resultado_teste_*.json`** - Resultados dos Testes
- ✅ Respostas bem-sucedidas
- ✅ Dados recebidos da API
- ✅ Tempo de execução

### 4. **`erro_teste_*.json`** - Erros dos Testes
- ✅ Detalhes de falhas
- ✅ Tipo de erro
- ✅ Contexto da falha

## 🚨 Tratamento Específico do Erro 10035

### O que é o Erro 10035?
O erro 10035 é um código de erro específico da API da Shopee que geralmente indica:
- **Rate limiting** (muitas requisições)
- **Problemas de autenticação**
- **Erros de formato de requisição**
- **Problemas temporários do servidor**

### Como é Tratado?
```python
def _handle_error_10035(self, response, attempt=1):
    """Trata especificamente o erro 10035 da Shopee"""
    # Log detalhado do erro
    # Extração de informações úteis
    # Sugestões de retry
    # Salvamento para análise
```

### Estratégias de Retry
- ✅ **Backoff exponencial**: Espera progressiva entre tentativas
- ✅ **Respeita headers**: Retry-After quando disponível
- ✅ **Múltiplas tentativas**: Até 3 tentativas por padrão
- ✅ **Logs detalhados**: Rastreamento completo do processo

## 📡 Headers Otimizados

### Headers Padrão
```python
headers = {
    "Content-Type": "application/json",
    "X-App-Id": app_id,
    "X-Timestamp": timestamp,
    "X-Signature": signature,
    "User-Agent": "ShopeeAffiliateAPI/1.0"
}
```

### Configurações de Sessão
- ✅ **Timeout configurável**: 30s conexão, 60s leitura
- ✅ **Retry automático**: Para códigos 429, 500, 502, 503, 504
- ✅ **Headers persistentes**: Mantidos entre requisições

## 🔍 Análise de Logs

### 1. **Verificar Log Principal**
```bash
# Visualizar log em tempo real
tail -f shopee_error_10035_debug.log

# Buscar por erros específicos
grep "ERROR" shopee_error_10035_debug.log

# Buscar por erro 10035
grep "10035" shopee_error_10035_debug.log
```

### 2. **Analisar Arquivo de Erro 10035**
```bash
# Ver detalhes do erro
cat erro_10035_detalhes.json | python -m json.tool

# Extrair mensagem do erro
cat erro_10035_detalhes.json | python -c "import json,sys; print(json.load(sys.stdin)['error_details']['message'])"
```

### 3. **Verificar Resultados dos Testes**
```bash
# Listar todos os resultados
ls -la resultado_teste_*.json

# Ver resultado específico
cat resultado_teste_1_teste_de_conexao_basica.json | python -m json.tool
```

## 📤 Enviando para o Suporte da Shopee

### Arquivos Essenciais
1. **`shopee_error_10035_debug.log`** - Log completo
2. **`erro_10035_detalhes.json`** - Detalhes específicos do erro
3. **`resultado_teste_*.json`** - Resultados dos testes
4. **`erro_teste_*.json`** - Erros capturados

### Informações Adicionais
- ✅ **App ID** usado nos testes
- ✅ **Timestamp** da ocorrência
- ✅ **Query GraphQL** que causou o erro
- ✅ **Headers** da requisição
- ✅ **Resposta completa** do servidor

## 🛠️ Solução de Problemas

### Erro de Importação
```bash
# Se der erro de módulo não encontrado
pip install -r requirements.txt

# Ou instalar manualmente
pip install requests urllib3
```

### Erro de Permissão
```bash
# No Windows, executar como administrador
# No Linux/Mac
chmod +x test_shopee_error_10035.py
```

### Logs não Gerados
```bash
# Verificar se o diretório tem permissão de escrita
# Verificar espaço em disco
# Verificar se o Python tem permissão para criar arquivos
```

## 🔄 Modo de Desenvolvimento

### Ativar Logs DEBUG
```python
# No início do script
logging.basicConfig(level=logging.DEBUG)

# Ou via variável de ambiente
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
```

### Testar Queries Específicas
```python
# Modificar test_cases no script
test_cases = [
    {
        "name": "Query Personalizada",
        "method": api.execute_query,
        "args": ["sua_query_aqui"],
        "description": "Descrição do teste"
    }
]
```

## 📈 Monitoramento em Tempo Real

### Executar com Logs em Tempo Real
```bash
# Terminal 1: Executar script
python test_shopee_error_10035.py

# Terminal 2: Monitorar logs
tail -f shopee_error_10035_debug.log

# Terminal 3: Monitorar arquivos de erro
watch -n 1 "ls -la *.json"
```

## 🎯 Próximos Passos

### 1. **Executar Testes**
- Rodar o script de teste
- Capturar logs completos
- Identificar padrões de erro

### 2. **Analisar Resultados**
- Verificar arquivos JSON gerados
- Identificar causa raiz do erro 10035
- Documentar padrões encontrados

### 3. **Enviar para Suporte**
- Compilar arquivos de log
- Incluir contexto completo
- Solicitar análise técnica

### 4. **Implementar Soluções**
- Ajustar rate limiting
- Otimizar queries
- Implementar fallbacks

## 📞 Suporte

### Arquivos para Enviar
- ✅ Log completo da execução
- ✅ Detalhes específicos do erro 10035
- ✅ Credenciais de teste (se solicitadas)
- ✅ Contexto da aplicação

### Informações Técnicas
- ✅ Versão do Python
- ✅ Sistema operacional
- ✅ Bibliotecas utilizadas
- ✅ Configurações de rede

---

**🎯 Objetivo**: Capturar o erro 10035 com logs detalhados para análise da equipe de suporte da Shopee.

**📋 Resultado**: Arquivos de log completos e detalhados para debug e resolução do problema.
