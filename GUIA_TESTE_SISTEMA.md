# 🧪 GUIA COMPLETO DE TESTE DO SISTEMA

## 🎯 **OBJETIVO**
Verificar se as correções das **imagens e nomes dos produtos** estão funcionando corretamente.

## 🚀 **OPÇÕES DE TESTE**

### **1️⃣ TESTE RÁPIDO (Recomendado para começar)**

```bash
python teste_rapido_oferta.py
```

**O que testa:**
- ✅ Importação dos módulos
- ✅ Criação de ofertas com estrutura correta
- ✅ Verificação das chaves necessárias

**Resultado esperado:**
- Sistema funcionando perfeitamente
- Todas as correções aplicadas com sucesso

---

### **2️⃣ TESTE DO SISTEMA PRINCIPAL**

```bash
python main.py
```

**O que testa:**
- ✅ Bot do Telegram funcionando
- ✅ Sistema de scrapers ativo
- ✅ Publicação automática de ofertas

**Como verificar:**
1. Execute o comando
2. Aguarde o bot inicializar
3. Verifique se está respondendo aos comandos
4. Use `/oferta` para testar publicação manual

---

### **3️⃣ TESTE DE PUBLICAÇÃO MANUAL**

**Comando no Telegram:**
```
/oferta https://www.exemplo.com/produto R$999,99 Nome do Produto
```

**O que testa:**
- ✅ Comando `/oferta` funcionando
- ✅ Formatação da mensagem
- ✅ Botões de ação
- ✅ Estrutura da oferta

---

### **4️⃣ TESTE DOS SCRAPERS INDIVIDUAIS**

#### **Teste Promobit:**
```bash
python promobit_scraper_clean.py
```

#### **Teste Amazon:**
```bash
python amazon_integration.py
```

#### **Teste AliExpress:**
```bash
python aliexpress_integration.py
```

---

## 🔍 **O QUE VERIFICAR**

### **✅ Estrutura da Oferta:**
- `titulo` - Nome do produto
- `preco` - Preço atual
- `preco_original` - Preço original (se houver)
- `url_produto` - URL do produto
- `url_afiliado` - URL de afiliado
- `imagem_url` - URL da imagem
- `loja` - Nome da loja
- `fonte` - Origem da oferta

### **✅ Mensagem no Telegram:**
- 📱 **Título** do produto aparecendo
- 🖼️ **Imagem** sendo exibida
- 💰 **Preço** formatado corretamente
- 🔗 **Botões de ação** funcionando
- 🏪 **Nome da loja** visível

---

## 🚨 **PROBLEMAS COMUNS E SOLUÇÕES**

### **❌ Erro: "Módulo não encontrado"**
**Solução:** Verifique se todas as dependências estão instaladas
```bash
pip install -r requirements.txt
```

### **❌ Erro: "Credenciais inválidas"**
**Solução:** Verifique o arquivo `config.py`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_USER_ID`

### **❌ Erro: "Timeout na API"**
**Solução:** Verifique a conexão com a internet e as APIs

---

## 📋 **CHECKLIST DE TESTE**

- [ ] **Teste rápido** executado com sucesso
- [ ] **Sistema principal** inicializando
- [ ] **Bot respondendo** aos comandos
- [ ] **Comando `/oferta`** funcionando
- [ ] **Imagens** sendo exibidas
- [ ] **Nomes dos produtos** aparecendo
- [ ] **Links de afiliado** funcionando
- [ ] **Botões de ação** ativos

---

## 🎉 **RESULTADO ESPERADO**

Após executar todos os testes, você deve ver:

1. **✅ Sistema funcionando perfeitamente**
2. **✅ Ofertas sendo postadas com imagens**
3. **✅ Nomes completos dos produtos**
4. **✅ Links de afiliado funcionando**
5. **✅ Botões de ação ativos**

---

## 💡 **PRÓXIMOS PASSOS**

1. **Execute o teste rápido** para verificar o básico
2. **Teste o sistema principal** para verificar em produção
3. **Use o comando `/oferta`** para testar publicação manual
4. **Verifique o canal** para confirmar que as ofertas estão sendo postadas corretamente

---

## 🆘 **PRECISA DE AJUDA?**

Se encontrar algum problema:
1. Verifique os logs de erro
2. Confirme se todas as dependências estão instaladas
3. Verifique as configurações no `config.py`
4. Execute o teste rápido para identificar o problema

**🎯 O sistema agora deve estar funcionando perfeitamente com imagens e nomes dos produtos!**
