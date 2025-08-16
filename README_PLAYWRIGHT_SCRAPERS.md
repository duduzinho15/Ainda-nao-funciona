# 🚀 Scrapers com Playwright - Sistema Unificado

## 📋 **Visão Geral**

Este sistema implementa scrapers modernos e eficientes para múltiplas lojas online usando **Playwright**, uma ferramenta da Microsoft que supera o Selenium em performance e confiabilidade.

## 🎯 **Por que Playwright?**

### ✅ **Vantagens sobre Selenium:**
- **Mais rápido** - Performance superior
- **Mais estável** - Melhor para sites modernos
- **Anti-detecção** - Contorna proteções anti-bot automaticamente
- **Auto-wait inteligente** - Aguarda elementos automaticamente
- **Suporte nativo** - Múltiplos navegadores sem drivers
- **API moderna** - Mais limpa e intuitiva

### ❌ **Desvantagens do Selenium:**
- Mais lento
- Problemas com JavaScript dinâmico
- Dificuldade para contornar proteções anti-bot
- Configuração complexa de drivers

## 🏗️ **Arquitetura do Sistema**

```
base_playwright_scraper.py          # Classe base com funcionalidades comuns
├── shopee_playwright_scraper.py    # Scraper da Shopee
├── amazon_playwright_scraper.py    # Scraper da Amazon
├── magalu_playwright_scraper.py    # Scraper do Magazine Luiza
├── promobit_playwright_scraper.py  # Scraper do Promobit
└── unified_playwright_scraper.py   # Scraper unificado (executa todos)
```

## 🚀 **Como Usar**

### **1. Instalação das Dependências**

```bash
# Instala o Playwright
pip install playwright

# Instala os navegadores necessários
playwright install
```

### **2. Teste Individual de Cada Loja**

#### **Shopee:**
```bash
python shopee_playwright_scraper.py
```

#### **Amazon:**
```bash
python amazon_playwright_scraper.py
```

#### **Magazine Luiza:**
```bash
python magalu_playwright_scraper.py
```

#### **Promobit:**
```bash
python promobit_playwright_scraper.py
```

### **3. Execução Unificada (Recomendado)**

```bash
python unified_playwright_scraper.py
```

O scraper unificado:
- ✅ Testa conexões com todas as lojas
- ✅ Executa scraping sequencial (mais estável)
- ✅ Salva resultados em arquivos JSON separados
- ✅ Gera relatório consolidado

## ⚙️ **Configurações**

### **Modo Headless vs Visível**
```python
# Modo headless (sem interface gráfica) - RECOMENDADO
scraper = ShopeePlaywrightScraper(headless=True)

# Modo visível (com interface gráfica) - Para debug
scraper = ShopeePlaywrightScraper(headless=False)
```

### **Delays e Rate Limiting**
```python
# Configurações na classe base
self.delay_between_requests = (2, 5)      # Delay entre páginas
self.delay_between_products = (0.3, 0.8)  # Delay entre produtos
self.max_products_per_page = 20           # Produtos por página
self.max_pages_per_category = 2           # Páginas por categoria
```

## 🔧 **Personalização**

### **Adicionar Nova Loja**

1. **Crie novo arquivo** seguindo o padrão:
```python
from base_playwright_scraper import BasePlaywrightScraper

class NovaLojaPlaywrightScraper(BasePlaywrightScraper):
    def __init__(self, headless: bool = True):
        super().__init__(
            base_url="https://nova-loja.com.br",
            store_name="Nova Loja",
            headless=headless
        )
        
        # Defina seletores específicos
        self.product_selectors = ['[class*="product"]']
        self.title_selectors = ['[class*="title"]']
        # ... outros seletores
```

2. **Adicione ao scraper unificado:**
```python
self.scrapers = {
    # ... scrapers existentes
    "Nova Loja": NovaLojaPlaywrightScraper(headless),
}
```

### **Modificar Categorias**
```python
self.categorias = [
    "smartphone",
    "notebook", 
    "fone de ouvido",
    # Adicione suas categorias aqui
    "nova_categoria"
]
```

## 📊 **Estrutura dos Dados**

### **Formato das Ofertas:**
```json
{
    "titulo": "Nome do Produto",
    "preco": "299.90",
    "link": "https://loja.com/produto",
    "imagem": "https://loja.com/imagem.jpg",
    "desconto": 15,
    "loja": "Nome da Loja",
    "categoria": "smartphone",
    "timestamp": 1640995200.0
}
```

### **Arquivos de Saída:**
- `ofertas_shopee_1234567890.json`
- `ofertas_amazon_1234567890.json`
- `ofertas_magalu_1234567890.json`
- `ofertas_promobit_1234567890.json`

## 🚨 **Solução de Problemas**

### **Erro: "Navegador não configurado"**
```bash
# Reinstale o Playwright
pip uninstall playwright
pip install playwright
playwright install
```

### **Erro: "Timeout aguardando elementos"**
- Aumente o timeout na classe base
- Verifique se os seletores ainda são válidos
- Use modo não-headless para debug

### **Performance Lenta**
- Reduza `max_pages_per_category`
- Aumente delays entre requests
- Use modo headless

## 🔒 **Considerações de Segurança**

### **Rate Limiting**
- Delays automáticos entre requests
- Comportamento humano simulado
- Scroll inteligente das páginas

### **Anti-Detecção**
- User agent realista
- Headers HTTP completos
- Remoção de indicadores de automação
- Viewport configurado

## 📈 **Monitoramento e Logs**

### **Níveis de Log:**
- `INFO`: Operações principais
- `WARNING`: Problemas não críticos
- `ERROR`: Falhas que impedem execução
- `DEBUG`: Informações detalhadas

### **Exemplo de Log:**
```
2025-08-14 10:30:00 - INFO - ✅ Navegador Playwright configurado para Shopee Brasil
2025-08-14 10:30:05 - INFO - 🔍 Buscando ofertas na categoria: smartphone
2025-08-14 10:30:10 - INFO - ✅ Página 1: 15 produtos encontrados
```

## 🎯 **Próximos Passos**

### **Melhorias Planejadas:**
1. **Proxy Rotation** - Para evitar bloqueios
2. **Machine Learning** - Detecção automática de seletores
3. **API REST** - Interface web para execução
4. **Scheduling** - Execução automática
5. **Database** - Armazenamento persistente
6. **Notificações** - Alertas de novas ofertas

### **Integração com Bot do Telegram:**
- Envio automático de ofertas
- Filtros por categoria/preço
- Alertas de preços baixos
- Histórico de ofertas

## 🤝 **Contribuição**

Para contribuir com melhorias:
1. Teste os scrapers existentes
2. Identifique problemas ou melhorias
3. Implemente as mudanças
4. Teste novamente
5. Documente as alterações

## 📞 **Suporte**

Em caso de problemas:
1. Verifique os logs de erro
2. Teste conexão individual com cada loja
3. Verifique se os seletores ainda são válidos
4. Consulte este README para soluções comuns

---

**🎉 Agora você tem um sistema de scraping moderno, eficiente e escalável!**
