# 🚀 Sistema de Recomendações de Ofertas Telegram

Sistema inteligente de postagem automática de ofertas no Telegram com cartões de imagem grande, formatação HTML e integração com múltiplas APIs de afiliados.

## ✨ **Características Principais**

### 🖼️ **Sistema de Cartão com Imagem Grande**
- **Download via bytes**: Imagens baixadas para evitar hotlinking
- **Fallback robusto**: Sistema de fallback em 3 níveis (bytes → URL → texto)
- **OG Image**: Extração automática de imagens de páginas web
- **Formatação HTML**: Títulos em negrito, preços destacados, emojis

### 🔗 **Integração com Afiliados**
- **AWIN**: IDs corretos (merchant vs publisher) configurados
- **Amazon**: Canonicalização de URLs e tags de afiliado
- **AliExpress**: API de afiliados integrada
- **Mercado Livre**: Sistema de afiliados configurado

### 🤖 **Bot do Telegram**
- **Cartões visuais**: Ofertas com imagem grande e formatação profissional
- **Botões inline**: "🛒 Comprar agora" e botões extras
- **Postagem automática**: Sistema de scraping e postagem automática
- **Comandos manuais**: `/oferta` para administradores

## 🏗️ **Arquitetura do Sistema**

```
📁 Sistema de Recomendações de Ofertas Telegram/
├── 🤖 Bot Principal
│   ├── main_simples.py          # Bot principal com polling manual
│   ├── telegram_poster.py       # Sistema de postagem melhorado
│   └── config.py                # Configurações e tokens
├── 🔍 Scrapers e APIs
│   ├── promobit_scraper_clean.py # Scraper do Promobit (funcionando)
│   ├── amazon_api.py            # API da Amazon
│   ├── awin_api.py              # API da AWIN corrigida
│   ├── affiliate.py             # Sistema de afiliados unificado
│   └── pelando_scraper.py       # Scraper do Pelando
├── 🛠️ Utilitários
│   ├── utils/images.py          # Download de imagens e OG
│   ├── database.py              # Sistema de banco de dados
│   └── run_scrapers.py          # Orquestrador de scrapers
└── 📚 Documentação
    ├── README.md                # Este arquivo
    └── scripts/post_sample.py   # Script de teste
```

## 🚀 **Instalação e Configuração**

### **1. Clone o repositório**
```bash
git clone https://github.com/seu-usuario/sistema-recomendacoes-ofertas-telegram.git
cd sistema-recomendacoes-ofertas-telegram
```

### **2. Crie um ambiente virtual**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### **3. Instale as dependências**
```bash
pip install -r requirements.txt
```

### **4. Configure as variáveis de ambiente**
Crie um arquivo `.env` na raiz do projeto:
```env
# Telegram
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
ADMIN_USER_ID=seu_user_id_aqui

# Amazon PA-API (opcional)
AMAZON_ACCESS_KEY=sua_access_key
AMAZON_SECRET_KEY=sua_secret_key
AMAZON_ASSOCIATE_TAG=sua_tag

# AWIN
AWIN_API_TOKEN=seu_token_awin

# Shopee (opcional)
SHOPEE_API_KEY=sua_api_key
SHOPEE_API_SECRET=sua_api_secret
SHOPEE_PARTNER_ID=seu_partner_id
```

## 🎯 **Como Usar**

### **Executar o Bot Principal**
```bash
python main_simples.py
```

### **Testar o Sistema de Postagem**
```bash
python scripts/post_sample.py
```

### **Executar Scrapers Individualmente**
```bash
python promobit_scraper_clean.py
python amazon_api.py
python awin_api.py
```

## 🔧 **Funcionalidades Implementadas**

### ✅ **Sistema de Postagem**
- [x] Cartões com imagem grande via `sendPhoto`
- [x] Download de imagens para bytes (anti-hotlinking)
- [x] Fallback para OG images
- [x] Fallback para texto sem preview
- [x] Formatação HTML com emojis
- [x] Botões inline "🛒 Comprar agora"

### ✅ **Integração AWIN**
- [x] IDs corretos (merchant vs publisher)
- [x] Mapeamento de lojas por slug
- [x] Helper `get_awin_merchant_id()`
- [x] Conversão automática de URLs

### ✅ **Scrapers Funcionais**
- [x] **Promobit**: 21 ofertas com preços e descontos
- [x] **Amazon**: API configurada
- [x] **AliExpress**: Sistema de afiliados
- [x] **Telegram**: Bot funcionando perfeitamente

### ✅ **Sistema de Fallback**
- [x] **Nível 1**: Imagem via bytes (mais robusto)
- [x] **Nível 2**: Imagem via URL direta
- [x] **Nível 3**: Texto sem preview

## 📊 **Exemplo de Oferta Postada**

```
🔥 Smartphone Motorola Edge 60 Pro 512GB Cinza 5G 24GB RAM 6,7"

💰 Preço: R$3.419,10
💸 De: R$ 4.999,00
🔥 Desconto: 31% OFF

🏷 Magazine Luiza | Promobit

[🛒 Comprar agora] [🔎 Ver detalhes]
```

## 🧪 **Testes**

### **Teste de Postagem**
```bash
python scripts/post_sample.py
```

Este script testa:
1. **Oferta com imagem explícita** → Imagem via bytes
2. **Oferta sem imagem mas com OG** → OG image extraída
3. **Oferta sem imagem/OG** → Texto sem preview

### **Teste do Sistema Completo**
```bash
python teste_sistema_final.py
```

## 🔍 **Logs e Monitoramento**

O sistema registra:
- **Origem da imagem**: 'offer', 'og:image', 'fallback:text'
- **IDs AWIN**: merchant_id e publisher_id usados
- **Status de postagem**: Sucesso/falha com detalhes
- **Performance**: Tempo de resposta e estatísticas

## 🚨 **Segurança**

- **Tokens nunca expostos** nos logs
- **disable_web_page_preview=True** em mensagens de texto
- **Validação de usuário** para comandos administrativos
- **Sanitização HTML** para evitar XSS

## 📈 **Performance**

- **Download paralelo** de imagens
- **Cache inteligente** para evitar re-downloads
- **Rate limiting** para APIs externas
- **Fallback robusto** para máxima disponibilidade

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 **Suporte**

- **Issues**: Abra uma issue no GitHub
- **Documentação**: Consulte os arquivos README específicos
- **Logs**: Verifique os logs para diagnóstico

## 🎉 **Status do Projeto**

**✅ COMPLETAMENTE FUNCIONAL!**

- **Sistema de postagem**: 100% implementado
- **Cartões com imagem**: 100% funcionando
- **Integração AWIN**: 100% corrigida
- **Fallback robusto**: 100% implementado
- **Formatação HTML**: 100% funcionando

---

**Desenvolvido com ❤️ para o canal @garimpeirogeek**
