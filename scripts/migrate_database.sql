-- scripts/migrate_database.sql
-- Migração e otimização do banco de dados para produção

-- Ativa modo WAL para melhor performance
PRAGMA journal_mode=WAL;

-- Cria índices para deduplicação rápida
CREATE INDEX IF NOT EXISTS idx_ofertas_hash ON ofertas(offer_hash);
CREATE INDEX IF NOT EXISTS idx_ofertas_data ON ofertas(created_at);
CREATE INDEX IF NOT EXISTS idx_ofertas_loja ON ofertas(loja);
CREATE INDEX IF NOT EXISTS idx_ofertas_url ON ofertas(url_produto);

-- Verifica se a coluna offer_hash existe
SELECT CASE 
    WHEN COUNT(*) > 0 THEN '✅ Coluna offer_hash já existe'
    ELSE '❌ Coluna offer_hash não existe - execute migrate_database.py'
END as status
FROM pragma_table_info('ofertas') 
WHERE name = 'offer_hash';

-- Verifica duplicatas
SELECT 
    offer_hash, 
    COUNT(*) as ocorrencias,
    GROUP_CONCAT(titulo, ' | ') as titulos
FROM ofertas 
WHERE offer_hash IS NOT NULL
GROUP BY offer_hash 
HAVING COUNT(*) > 1;

-- Estatísticas do banco
SELECT 
    COUNT(*) as total_ofertas,
    COUNT(DISTINCT offer_hash) as hashes_unicos,
    COUNT(DISTINCT loja) as lojas_unicas,
    MIN(created_at) as primeira_oferta,
    MAX(created_at) as ultima_oferta
FROM ofertas;
