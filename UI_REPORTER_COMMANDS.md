# UI Reporter - Comandos Úteis

## 🚀 Comandos para Desenvolvimento

### Snapshot human-readable + arquivo
```bash
python -m app.dashboard --report
```
- Gera snapshot visual ASCII
- Salva em `ui_snapshot.txt`
- Mostra todos os checks de aceite

### JSON para máquinas
```bash
python -m app.dashboard --report --json > ui_summary.json
```
- Gera saída JSON estruturada
- Útil para parsing automático
- Salva em arquivo para análise

### Modo CI: falha se check reprovar e encerra
```bash
python -m app.dashboard --report --strict --exit-after-report
```
- Executa todos os checks
- Falha (exit code != 0) se algum check reprovar
- Encerra automaticamente após o report
- Ideal para CI/CD

## 🔧 Comandos para CI/CD

### Verificação de snapshot baseline
```bash
python diagnostics/verify_snapshot.py
```
- Compara snapshot atual com baseline
- Falha se houver mudanças visuais
- Mostra diff detalhado se houver diferenças

### Atualizar baseline (após mudanças intencionais)
```bash
copy ui_snapshot.txt tests\baselines\ui_snapshot.txt
```

## 🌍 Variáveis de Ambiente

### GG_REPORT=1
- Ativa o UI Reporter automaticamente
- Equivalente a `--report`

### GG_STRICT=1
- Ativa strict mode automaticamente
- Falha se checks reprovarem
- Equivalente a `--strict`

### GG_EXIT_AFTER_REPORT=1
- Encerra automaticamente após report
- Equivalente a `--exit-after-report`

## 📊 Exemplos de Uso

### Desenvolvimento local
```bash
# Verificar UI sem encerrar
python -m app.dashboard --report

# Verificar e falhar se algo estiver errado
python -m app.dashboard --report --strict
```

### CI/CD Pipeline
```bash
# Executar e falhar se necessário
python -m app.dashboard --report --strict --exit-after-report

# Verificar baseline
python diagnostics/verify_snapshot.py
```

### Debugging
```bash
# Apenas JSON para análise
python -m app.dashboard --report --json

# Com variáveis de ambiente
set GG_REPORT=1
set GG_STRICT=1
python -m app.dashboard
```

## 🔍 Códigos de Saída

- **0**: Sucesso, todos os checks passaram
- **1**: Erro no UI Reporter (strict mode)
- **2**: Checks reprovaram (strict mode)
- **3**: Arquivos de snapshot ausentes
- **4**: Snapshot mudou (diff detectado)

## 📁 Arquivos Gerados

- `ui_snapshot.txt`: Snapshot visual ASCII + checks
- `ui_summary.json`: Resumo estruturado em JSON
- `tests/baselines/ui_snapshot.txt`: Baseline aprovado

## 🚨 Troubleshooting

### Erro de importação
```bash
# Verificar se o path está correto
python -c "import diagnostics.ui_reporter; print('OK')"
```

### Checks falhando
```bash
# Verificar quais checks falharam
python -m app.dashboard --report --json | python -c "import json,sys; data=json.load(sys.stdin); [print(f'{k}: {\"✅\" if v else \"❌\"}') for k,v in data['checks'].items()]"
```

### Baseline desatualizado
```bash
# Atualizar baseline
copy ui_snapshot.txt tests\baselines\ui_snapshot.txt
```
