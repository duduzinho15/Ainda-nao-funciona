# Integração Rakuten (LinkSynergy) - Placeholder

## 📋 **Status Atual**
- **Status**: Placeholder - Não ativo ainda
- **Tipo**: Integração futura via LinkSynergy
- **Prioridade**: Baixa - Aguardando aprovação

## 🔗 **Padrão de Deeplink**
```
https://click.linksynergy.com/deeplink?id=<PUBLISHER_ID>&mid=<MID>&murl=<URL_ENCODED>&u1=<SUBID>
```

### Parâmetros:
- `id`: ID do publisher/afiliado (a preencher)
- `mid`: Merchant ID da loja (a preencher)
- `murl`: URL de destino (encoded)
- `u1`: Sub-ID para tracking (opcional)

## 📊 **Configurações Pendentes**

### Publisher ID
```
PUBLISHER_ID = ""  # A preencher quando houver aprovação
```

### Merchant IDs (MIDs)
```
MIDS = {
    "amazon": "",      # Amazon Brasil
    "walmart": "",     # Walmart Brasil
    "bestbuy": "",     # Best Buy Brasil
    # Adicionar conforme aprovações
}
```

## 🚀 **Implementação Futura**

### 1. Arquivo de Configuração
```python
# src/affiliate/rakuten.py
class RakutenAffiliateBuilder:
    def __init__(self, publisher_id: str, merchant_id: str, sub_id: Optional[str] = None):
        self.publisher_id = publisher_id
        self.merchant_id = merchant_id
        self.sub_id = sub_id or ""
    
    def build_deeplink(self, target_url: str) -> str:
        # Implementar quando aprovado
        pass
```

### 2. Ativação no Pipeline
```python
# src/core/platforms.py
"rakuten": PlatformConfig(
    name="Rakuten (LinkSynergy)",
    type=PlatformType.RAKUTEN,
    active=True,  # Mudar para True quando aprovado
    affiliate_enabled=True,
    scraper_enabled=True,
    description="Integração ativa com LinkSynergy"
)
```

## ⚠️ **Importante**
- **NÃO habilitar** no pipeline até aprovação real
- **NÃO gerar** links de afiliado sem credenciais válidas
- **NÃO fazer** scraping de lojas sem permissão

## 📞 **Contatos para Aprovação**
- **Rede**: Rakuten LinkSynergy
- **Região**: Brasil
- **Tipo**: Programa de Afiliados
- **Status**: Pendente de contato inicial

## 🔄 **Próximos Passos**
1. Contatar Rakuten LinkSynergy Brasil
2. Solicitar credenciais de publisher
3. Obter lista de merchants aprovados
4. Implementar builder de deeplinks
5. Testar com URLs de exemplo
6. Ativar no pipeline de produção

## 📚 **Referências**
- [LinkSynergy Publisher Portal](https://publishers.rakuten.com/)
- [LinkSynergy Deeplink Documentation](https://publishers.rakuten.com/deeplink)
- [Rakuten Brasil](https://www.rakuten.com.br/)
