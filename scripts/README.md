# 📚 Scripts do Garimpeiro Geek

Este diretório contém scripts utilitários para o sistema Garimpeiro Geek.

## 🚀 Scripts Disponíveis

### 1. `post_sample.py` - Teste de Publicação
**Objetivo:** Testa o sistema de publicação no Telegram com diferentes cenários de imagem.

**Funcionalidades:**
- Testa 3 cenários: imagem explícita, OG image, sem imagem
- Valida formatação HTML e botões
- Testa fallbacks de imagem
- Publica no chat de teste configurado

**Uso:**
```bash
python scripts/post_sample.py
```

**Saída Esperada:**
- Mensagens publicadas no chat de teste
- Logs de console com IDs das mensagens
- Validação visual da formatação

---

### 2. `test_cache_dedupe.py` - Teste do Sistema de Cache e Deduplicação
**Objetivo:** Valida o sistema completo de cache TTL e deduplicação de ofertas.

**Funcionalidades Testadas:**
1. **Sistema de Cache TTL:**
   - Set/get de valores
   - Expiração automática
   - Estatísticas do cache
   - Limpeza de entradas expiradas

2. **Sistema de Hash de Ofertas:**
   - Geração de hashes únicos
   - Normalização de dados
   - Validação de ofertas
   - Detecção de similares

3. **Cache de Imagens:**
   - Performance de requisições repetidas
   - Melhoria de latência
   - Funcionamento do decorator @cached

4. **Sistema de Deduplicação:**
   - Hash de ofertas similares
   - Detecção de duplicatas
   - Validação de hashes únicos

5. **Coalescência de Requisições:**
   - Agrupamento de requisições simultâneas
   - Evita requisições duplicadas
   - Performance em cenários concorrentes

6. **Melhoria de Performance:**
   - Comparação com/sem cache
   - Métricas de melhoria
   - Validação de funcionamento

**Uso:**
```bash
python scripts/test_cache_dedupe.py
```

**Saída Esperada:**
- Todos os 6 testes passando
- Logs detalhados de cada funcionalidade
- Estatísticas finais do cache
- Métricas de performance

**Cenários de Teste:**
- **Cache TTL:** Valida expiração e limpeza automática
- **Hash de Ofertas:** Testa normalização e geração de hashes
- **Cache de Imagens:** Verifica melhoria de performance
- **Deduplicação:** Valida detecção de ofertas similares
- **Coalescência:** Testa agrupamento de requisições
- **Performance:** Mede ganhos com cache

---

### 3. `migrate_database.py` - Migração do Banco de Dados
**Objetivo:** Adiciona coluna `offer_hash` ao banco existente e migra dados.

**Funcionalidades:**
1. **Verificação:** Checa se coluna já existe
2. **Migração:** Adiciona coluna se necessário
3. **Processamento:** Gera hashes para ofertas existentes
4. **Validação:** Verifica integridade da migração
5. **Índices:** Cria índice único para offer_hash

**Uso:**
```bash
python scripts/migrate_database.py
```

**Saída Esperada:**
- Coluna offer_hash criada/verificada
- Hashes gerados para ofertas existentes
- Índice único criado
- Validação bem-sucedida
- Estatísticas da migração

**⚠️ Importante:**
- Execute este script antes de usar o sistema de deduplicação
- Faça backup do banco antes da migração
- O script é idempotente (pode ser executado múltiplas vezes)

---

## 🔧 Configuração dos Scripts

### Variáveis de Ambiente Necessárias:
```bash
# Para post_sample.py
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_TEST_CHAT_ID=seu_chat_de_teste_aqui

# Para migrate_database.py
DB_NAME=ofertas.db  # Nome do banco de dados
```

### Dependências:
```bash
pip install -r requirements.txt
```

---

## 📊 Interpretação dos Resultados

### Teste de Cache e Deduplicação:
- **✅ Todos os testes passando:** Sistema funcionando perfeitamente
- **⚠️ Alguns testes com avisos:** Funcionamento correto com observações
- **❌ Testes falhando:** Problemas que precisam ser investigados

### Métricas de Performance:
- **Melhoria > 50%:** Cache funcionando perfeitamente
- **Melhoria 20-50%:** Cache funcionando bem
- **Melhoria < 20%:** Cache com ganhos limitados
- **Sem melhoria:** Possível problema na implementação

### Logs de Deduplicação:
- **🔐 Hash gerado:** Oferta processada com sucesso
- **⚠️ Oferta duplicada:** Sistema detectou duplicata
- **✅ Deduplicação funcionando:** Hashes similares geram mesmo valor

---

## 🚨 Troubleshooting

### Problemas Comuns:

1. **Erro de importação:**
   ```bash
   # Certifique-se de estar no diretório raiz do projeto
   cd /caminho/para/garimpeiro-geek
   python scripts/test_cache_dedupe.py
   ```

2. **Banco de dados não encontrado:**
   ```bash
   # Verifique se o arquivo do banco existe
   ls -la *.db
   # Execute a migração primeiro
   python scripts/migrate_database.py
   ```

3. **Erro de permissão:**
   ```bash
   # Verifique permissões do diretório
   chmod +x scripts/*.py
   ```

4. **Cache não funcionando:**
   ```bash
   # Verifique logs de debug
   # Limpe o cache e teste novamente
   python -c "from utils.cache import get_cache; asyncio.run(get_cache().clear())"
   ```

---

## 📈 Monitoramento e Métricas

### Estatísticas do Cache:
- **Total de entradas:** Número total de itens no cache
- **Entradas ativas:** Itens não expirados
- **Entradas expiradas:** Itens que expiraram
- **Requisições pendentes:** Requisições em coalescência
- **Total de acessos:** Número total de hits
- **Média de acessos:** Média de acessos por entrada
- **Uso de memória:** Consumo de RAM em MB

### Logs de Deduplicação:
- **Hash gerado:** Confirmação de hash único
- **Oferta duplicada:** Detecção de duplicatas
- **Componentes normalizados:** Dados usados para hash
- **Validação:** Confirmação de dados corretos

---

## 🔄 Fluxo de Trabalho Recomendado

1. **Primeira execução:**
   ```bash
   python scripts/migrate_database.py
   python scripts/test_cache_dedupe.py
   ```

2. **Testes regulares:**
   ```bash
   python scripts/test_cache_dedupe.py
   ```

3. **Validação de publicação:**
   ```bash
   python scripts/post_sample.py
   ```

4. **Monitoramento contínuo:**
   - Verifique logs de deduplicação
   - Monitore estatísticas do cache
   - Valide performance das imagens

---

## 📚 Documentação Adicional

- **Sistema de Cache:** `utils/cache.py`
- **Hash de Ofertas:** `utils/offer_hash.py`
- **Banco de Dados:** `database.py`
- **Publicação:** `telegram_poster.py`
- **Templates:** `posting/message_templates.py`

---

## 🎯 Próximos Passos

1. **Integração com scrapers:** Garantir que todos os scrapers usem offer_hash
2. **Monitoramento automático:** Implementar alertas para problemas de cache
3. **Métricas avançadas:** Dashboard de performance do sistema
4. **Testes automatizados:** CI/CD para validação contínua
5. **Otimizações:** Ajuste de TTLs baseado em uso real
