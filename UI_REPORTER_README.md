# 🛠️ UI Reporter - Sistema de Diagnósticos do Dashboard

## 📋 Visão Geral

O **UI Reporter** é uma ferramenta de diagnóstico que permite testar o dashboard Flet sem interface gráfica, ideal para CI/CD, testes automatizados e debugging.

## 🚀 Como Usar

### Execução Básica
```bash
# Gerar relatório completo
python app/dashboard.py --report

# Gerar relatório com saída JSON
python app/dashboard.py --report --json

# Encerrar após relatório (útil para CI)
python app/dashboard.py --report --exit-after-report
```

### Variáveis de Ambiente
```bash
# Ativar relatório
export GG_REPORT=1
python app/dashboard.py

# Encerrar após relatório
export GG_EXIT_AFTER_REPORT=1
python app/dashboard.py --report
```

## 📊 O que o Reporter Analisa

### ✅ Checks de Aceite
1. **tem_tabs** - Verifica se há abas funcionais
2. **tem_quatro_cards** - Confirma 4 cards de métricas
3. **tem_filtros_periodo** - Valida filtros de período
4. **tem_toggle_tema** - Testa alternador de tema
5. **tem_painel_grafico** - Verifica painel do gráfico
6. **tem_painel_logs** - Confirma painel de logs

### 🔍 Análise Técnica
- **Controles únicos**: Conta componentes não duplicados
- **Top tipos**: Lista tipos de controles mais usados
- **Árvore de controles**: Mapeia hierarquia completa da UI

### 🎨 Snapshot Visual
- **Representação ASCII** da interface
- **Estado dos componentes** (selecionado, ativo, etc.)
- **Estrutura hierárquica** dos elementos

## 📁 Arquivos Gerados

### ui_snapshot.txt
```
┌ Garimpeiro Geek - Dashboard  (Tema: Dark)
├ Tabs: [*] Logs | [ ] Configurações | [ ] Controles
├ Cards:
│  • Lojas ativas → 10
│  • Ofertas → 14
│  • Período → ALL
│  • Preço médio → R$ 157,91
├ Filtros: [24h]  [7 dias]  [30 dias]  [✓ Tudo]
├ Gráfico: Distribuição por Loja (painel encontrado)
└ Logs: painel encontrado

CHECKS:
- tem_tabs: OK
- tem_quatro_cards: OK
- tem_filtros_periodo: OK
- tem_toggle_tema: OK
- tem_painel_grafico: OK
- tem_painel_logs: OK
```

## 🏗️ Arquitetura

### diagnostics/ui_reporter.py
- **Função principal**: `dump_report(page, json_summary=False)`
- **Introspecção**: Navega pela árvore de controles Flet
- **Validação**: Executa checks de aceite automáticos
- **Formatação**: Gera saída visual e JSON

### Integração no Dashboard
```python
# Em app/dashboard.py
want_report = ("--report" in sys.argv) or os.getenv("GG_REPORT") == "1"
if want_report:
    from diagnostics.ui_reporter import dump_report
    dump_report(page, json_summary=("--json" in sys.argv))
```

## 🎯 Casos de Uso

### 1. **CI/CD Pipeline**
```yaml
# .github/workflows/test.yml
- name: Test Dashboard UI
  run: |
    export GG_REPORT=1
    export GG_EXIT_AFTER_REPORT=1
    python app/dashboard.py --report
```

### 2. **Testes Locais**
```bash
# Verificar se a UI está funcionando
python app/dashboard.py --report

# Debug de componentes específicos
python app/dashboard.py --report --json | jq '.checks'
```

### 3. **Validação de Deploy**
```bash
# Verificar se todos os checks passaram
python app/dashboard.py --report | grep "✅"
```

## 🔧 Dependências

### Obrigatórias
- `flet>=0.28.3` - Framework UI
- `python>=3.11` - Runtime Python

### Opcionais
- `rich>=13.0.0` - Formatação colorida no terminal

## 📝 Exemplo de Saída JSON

```json
{
  "flet_version": "unknown",
  "control_types": {
    "Column": 11,
    "Container": 25,
    "Row": 9,
    "Text": 16,
    "IconButton": 1,
    "Tabs": 1,
    "Tab": 3,
    "Icon": 6,
    "Divider": 1,
    "ResponsiveRow": 1,
    "CupertinoButton": 4
  },
  "checks": {
    "tem_tabs": true,
    "tem_quatro_cards": true,
    "tem_filtros_periodo": true,
    "tem_toggle_tema": true,
    "tem_painel_grafico": true,
    "tem_painel_logs": true
  },
  "has_rich": true,
  "snapshot": "...",
  "output_file": "ui_snapshot.txt"
}
```

## 🚨 Troubleshooting

### Erro: "Module not found: diagnostics"
```bash
# Verificar se o diretório existe
ls -la diagnostics/

# Verificar se __init__.py está presente
ls -la diagnostics/__init__.py
```

### Erro: "Unknown control"
- **Causa**: Componentes customizados herdando de `ft.Control`
- **Solução**: Usar `ft.UserControl` ou funções que retornam controles nativos

### Relatório vazio
- **Verificar**: Se o dashboard está renderizando corretamente
- **Testar**: Executar `python app/dashboard.py` sem `--report`

## 🔮 Próximos Passos

1. **Adicionar mais checks** de aceite específicos
2. **Implementar comparação** entre snapshots
3. **Adicionar métricas** de performance da UI
4. **Integrar com testes** automatizados
5. **Criar dashboard** de saúde da interface

## 📞 Suporte

Para dúvidas ou problemas com o UI Reporter:
1. Verificar logs de erro no terminal
2. Executar com `--json` para debug detalhado
3. Verificar se todos os componentes têm `key` definida
4. Confirmar que o Flet está funcionando normalmente

---

**Desenvolvido para o Sistema Garimpeiro Geek** 🚀
