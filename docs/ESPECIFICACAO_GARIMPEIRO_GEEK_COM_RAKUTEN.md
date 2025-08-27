# Garimpeiro Geek — Especificação com Integração Rakuten

Este documento descreve **todas as regras, arquitetura e funcionamento** do projeto de recomendação de ofertas via Telegram, incluindo a integração Rakuten Advertising.

---

## 📌 Objetivo
Organizar de forma definitiva o projeto **Garimpeiro Geek**, garantindo:
- Estrutura de pastas limpa e imutável
- Regras que o Cursor deve sempre seguir
- Especificações de scraping e afiliados
- **Integração Rakuten com feature flag**
- Fluxo completo (descoberta → enriquecimento → link afiliado → postagem → métricas)
- Orientações de testes e checklists
- Especificação do Dashboard Flet para observabilidade

---

## 🔗 Afiliações Ativas

### **Awin (Deeplinks)**
- **Comfy BR** - MID: 23377, AFFID: 2370719
- **Trocafy** - MID: 51277, AFFID: 2370719  
- **LG Brasil** - MID: 33061, AFFID: 2370719
- **KaBuM!** - MID: 17729, AFFID: 2370719
- **Ninja** - MID: 106765, AFFID: 2370719
- **Samsung** - MID: 25539, AFFID: 2510157

### **Outras Plataformas**
- **Mercado Livre** - Shortlinks + etiqueta `garimpeirogeek`
- **Magazine Luiza** - Vitrine `magazinegarimpeirogeek`
- **Amazon** - Tag `garimpeirogee-20`
- **Shopee** - Shortlinks via painel + cache
- **AliExpress** - Shortlinks via portal + cache (tracking: "telegram")

### **Rakuten Advertising** ⭐ NOVO
- **Status**: Integrado com feature flag
- **Padrão**: Desabilitado (`RAKUTEN_ENABLED=false`)
- **Formato**: `https://click.linksynergy.com/deeplink?id=<id>&mid=<mid>&murl=<url>&u1=<subid>`
- **Lojas Suportadas**: Hype Games, Nuuvem (configuráveis)

---

## 🚀 Integração Rakuten

### **Configuração**

#### **Variáveis de Ambiente (.env)**
```bash
# Rakuten (desabilitado por padrão)
RAKUTEN_ENABLED=false
RAKUTEN_WEBSERVICE_TOKEN=b64c55b9b35ee0e881a8f7bafeb77a374b11e62e439ec63cd4470dbbefef4409
RAKUTEN_SECURITY_TOKEN=65d854a458c9a1e4be4e7c93e0631c704fe842c37022a82d398d4390ca2f596d
RAKUTEN_SID=  # Opcional, específico por loja/programa
```

#### **Como Ativar**
1. Edite o arquivo `.env`
2. Configure `RAKUTEN_ENABLED=true`
3. Adicione os tokens obrigatórios
4. Reinicie o sistema

#### **Como Desativar**
1. Configure `RAKUTEN_ENABLED=false`
2. Ou remova as variáveis do `.env`

### **Funcionalidades**

#### **Cliente Rakuten (`RakutenClient`)**
```python
from src.affiliate.rakuten import get_rakuten_client

# Obter cliente configurado
client = get_rakuten_client()

if client:
    # Verificar saúde
    if client.healthcheck():
        # Gerar deeplink
        deeplink = client.build_deeplink("https://exemplo.com/produto")
    else:
        print("Cliente Rakuten não está saudável")
else:
    print("Rakuten não está configurado")
```

#### **Builder de Compatibilidade (`RakutenAffiliateBuilder`)**
```python
from src.affiliate.rakuten import build_rakuten_link

try:
    deeplink = build_rakuten_link(
        target_url="https://exemplo.com/produto",
        affiliate_id="meu_id",
        merchant_id="merchant_id"
    )
except FeatureDisabledError:
    print("Rakuten está desabilitado")
```

### **Smoke Test**

#### **1. Verificar Configuração**
```bash
# Verificar se feature flag está ativo
python -c "from src.core.settings import Settings; print(f'Rakuten enabled: {Settings.RAKUTEN_ENABLED}')"
```

#### **2. Testar Healthcheck**
```python
from src.affiliate.rakuten import get_rakuten_client

client = get_rakuten_client()
if client:
    print(f"Healthcheck: {client.healthcheck()}")
    print(f"Config: {client.get_config_info()}")
else:
    print("Cliente não disponível")
```

#### **3. Testar Geração de Deeplink**
```python
from src.affiliate.rakuten import get_rakuten_client

client = get_rakuten_client()
if client:
    deeplink = client.build_deeplink("https://exemplo.com/produto")
    print(f"Deeplink gerado: {deeplink}")
    
    # Verificar formato
    assert deeplink.startswith("https://click.linksynergy.com/deeplink")
    assert "id=" in deeplink
    assert "mid=" in deeplink
    assert "murl=" in deeplink
    assert "u1=" in deeplink
```

### **Tratamento de Erros**

#### **Feature Disabled**
```python
from src.affiliate.rakuten import FeatureDisabledError

try:
    deeplink = client.build_deeplink("https://exemplo.com")
except FeatureDisabledError:
    print("Rakuten está desabilitado. Configure RAKUTEN_ENABLED=true")
```

#### **API Inacessível**
- Sistema automaticamente cai para fallback local
- Logs de WARNING são gerados
- Deeplinks locais são retornados como backup

#### **Tokens Inválidos**
- Healthcheck retorna `False`
- Erro é logado
- Sistema não permite operações

---

## 🧪 Testes Rakuten

### **Executar Testes Específicos**
```bash
# Apenas testes Rakuten
make test-aff

# Ou diretamente
pytest src/tests/test_rakuten_flag.py -v
```

### **Cobertura de Testes**
- ✅ Feature flag desabilitado por padrão
- ✅ Feature flag habilitado funciona
- ✅ Healthcheck com/sem tokens
- ✅ Geração de deeplinks
- ✅ Fallback para API local
- ✅ Tratamento de erros
- ✅ Validação de URLs

---

## 🔧 Arquitetura Rakuten

### **Componentes**

#### **1. `RakutenClient` (Principal)**
- Gerenciamento de sessão
- Healthcheck da API
- Fallback para geração local
- Configuração via `.env`

#### **2. `RakutenAffiliateBuilder` (Compatibilidade)**
- Mantido para código existente
- Verifica feature flag
- Lança `FeatureDisabledError` se desabilitado

#### **3. `get_rakuten_client()` (Factory)**
- Retorna cliente configurado ou `None`
- Valida tokens obrigatórios
- Verifica feature flag

### **Fluxo de Operação**

```
1. Verificar RAKUTEN_ENABLED
   ↓
2. Se false → FeatureDisabledError
   ↓
3. Se true → Verificar tokens
   ↓
4. Se tokens OK → Tentar API real
   ↓
5. Se API OK → Retornar deeplink real
   ↓
6. Se API falha → Fallback local
   ↓
7. Retornar deeplink (real ou local)
```

---

## 📊 Monitoramento

### **Métricas Disponíveis**
- Status do feature flag
- Configuração de tokens
- Saúde do cliente
- Uso de fallback local
- Erros de API

### **Logs Estruturados**
```python
# Exemplo de log
logger.info("Deeplink Rakuten local gerado: https://click.linksynergy.com/deeplink?id=...")
logger.warning("API Rakuten não acessível, usando construtor local")
logger.error("Erro ao gerar deeplink Rakuten: API timeout")
```

---

## 🚨 Troubleshooting

### **Problemas Comuns**

#### **1. Feature Disabled Error**
```
FeatureDisabledError: Rakuten está desabilitado. Configure RAKUTEN_ENABLED=true no .env
```
**Solução**: Configure `RAKUTEN_ENABLED=true` no `.env`

#### **2. Tokens Não Configurados**
```
logger.warning("Tokens Rakuten não configurados")
```
**Solução**: Adicione `RAKUTEN_WEBSERVICE_TOKEN` e `RAKUTEN_SECURITY_TOKEN` no `.env`

#### **3. Cliente Não Saudável**
```
logger.warning("Cliente Rakuten não está saudável")
```
**Solução**: Verifique conectividade de rede e validade dos tokens

#### **4. API Inacessível**
```
logger.warning("API Rakuten não acessível, usando construtor local")
```
**Solução**: Sistema funciona com fallback local. Verifique conectividade se precisar da API real.

---

## 🔮 Roadmap Rakuten

### **Fase 1 (Atual)**
- ✅ Feature flag implementado
- ✅ Cliente básico funcionando
- ✅ Fallback local implementado
- ✅ Testes de cobertura completa

### **Fase 2 (Próxima)**
- 🔄 Integração com API real
- 🔄 Suporte a múltiplas lojas
- 🔄 Cache de deeplinks
- 🔄 Métricas avançadas

### **Fase 3 (Futura)**
- 📊 Dashboard de performance
- 📊 Relatórios automáticos
- 📊 Alertas de saúde
- 📊 Integração com CI/CD

---

## 📚 Referências

### **Documentação Rakuten**
- [Rakuten Marketing Developer Portal](https://developers.rakutenmarketing.com/)
- [LinkSynergy API Documentation](https://developers.rakutenmarketing.com/linksynergy/)
- [Deeplink Format Specification](https://developers.rakutenmarketing.com/linksynergy/deeplink/)

### **Tokens de Exemplo**
- **Webservice Token**: `b64c55b9b35ee0e881a8f7bafeb77a374b11e62e439ec63cd4470dbbefef4409`
- **Security Token**: `65d854a458c9a1e4be4e7c93e0631c704fe842c37022a82d398d4390ca2f596d`

### **Lojas Configuradas**
- **Hype Games**: MID 53304, Group offer ID: 1799190
- **Nuuvem**: MID 46796, Group offer ID: 1692636

---

## ✅ Checklist de Implementação

- [x] Feature flag implementado
- [x] Cliente Rakuten criado
- [x] Fallback local implementado
- [x] Testes de cobertura completa
- [x] Documentação atualizada
- [x] Integração com sistema de postagem
- [x] Validação de URLs implementada
- [x] Logs estruturados
- [x] Métricas básicas
- [ ] API real integrada
- [ ] Cache de deeplinks
- [ ] Dashboard de monitoramento

---

**📅 Última Atualização**: Dezembro 2024  
**👥 Responsável**: Equipe de Desenvolvimento  
**📧 Contato**: [Seu Email]  
**🔗 Repositório**: [URL do GitHub]
