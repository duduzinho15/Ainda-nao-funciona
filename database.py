import sqlite3
import config
from datetime import datetime
import re
from typing import Optional, List, Dict, Any

def setup_database():
    """
    Cria as tabelas necessárias no banco de dados, se não existirem.
    
    Tabelas criadas:
    - ofertas: Armazena todas as ofertas publicadas
    - configuracoes: Armazena configurações do sistema
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Tabela de ofertas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ofertas (
            id_produto TEXT NOT NULL,         -- ID único do produto na loja (SKU, ASIN, etc.)
            loja TEXT NOT NULL,                -- Nome da loja (ex: 'Magazine Luiza', 'Amazon')
            titulo TEXT NOT NULL,              -- Título do produto
            preco TEXT NOT NULL,               -- Preço atual formatado como string
            preco_original TEXT,               -- Preço original (antes do desconto)
            url_produto TEXT NOT NULL,         -- URL canônica do produto
            url_afiliado TEXT,                 -- URL de afiliado (quando aplicável)
            url_imagem TEXT,                   -- URL da imagem do produto
            fonte TEXT NOT NULL,               -- Fonte da oferta (ex: 'Scraper', 'Manual')
            offer_hash TEXT,                   -- Hash único da oferta para deduplicação
            data_postagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_produto, loja)     -- Chave primária composta
        )
        ''')
        
        # Índices para melhorar a performance das buscas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loja ON ofertas(loja)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fonte ON ofertas(fonte)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_postagem ON ofertas(data_postagem)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asin ON ofertas(asin)')  # Índice para buscas por ASIN
        
        # Índice único para offer_hash (deduplicação)
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_ofertas_offer_hash ON ofertas(offer_hash)')
        
        # Tabela de configurações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT,
            descricao TEXT,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Inserir configurações padrão, se não existirem
        cursor.execute('''
        INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
        VALUES (?, ?, ?)
        ''', ('ultima_atualizacao', '2000-01-01 00:00:00', 'Data da última atualização de ofertas'))
        
        conn.commit()
        print("✅ Banco de dados configurado com sucesso.")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao configurar o banco de dados: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def extrair_dominio_loja(url: str) -> str:
    """
    Extrai o domínio principal da URL para identificar a loja.
    
    Args:
        url: URL completa do produto
        
    Returns:
        str: Domínio da loja (ex: 'amazon.com.br', 'magazineluiza.com.br')
    """
    import urllib.parse
    from urllib.parse import urlparse
    
    try:
        domain = urlparse(url).netloc.lower()
        # Remove www. se existir
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        print(f"Erro ao extrair domínio da URL {url}: {e}")
        return "desconhecido"

def oferta_ja_existe(id_produto: str, loja: str) -> bool:
    """
    Verifica se uma oferta já existe no banco de dados com base no ID do produto e na loja.
    
    Args:
        id_produto: ID único do produto na loja
        loja: Nome da loja (ex: 'Magazine Luiza', 'Amazon')
        
    Returns:
        bool: True se a oferta já existe, False caso contrário
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT 1 FROM ofertas WHERE id_produto = ? AND loja = ?',
            (id_produto, loja)
        )
        
        return cursor.fetchone() is not None
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao verificar oferta existente: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def oferta_ja_existe_por_hash(offer_hash: str) -> bool:
    """
    Verifica se uma oferta já existe no banco de dados com base no hash da oferta.
    
    Args:
        offer_hash: Hash único da oferta
        
    Returns:
        bool: True se a oferta já existe, False caso contrário
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT 1 FROM ofertas WHERE offer_hash = ?',
            (offer_hash,)
        )
        
        return cursor.fetchone() is not None
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao verificar oferta por hash: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def adicionar_oferta(oferta: dict) -> bool:
    """
    Adiciona uma nova oferta ao banco de dados.
    
    Args:
        oferta: Dicionário contendo os dados da oferta com as seguintes chaves:
            - id_produto: ID único do produto na loja (obrigatório)
            - loja: Nome da loja (ex: 'Magazine Luiza') (obrigatório)
            - titulo: Título do produto (obrigatório)
            - preco: Preço atual formatado como string (obrigatório)
            - url_produto: URL canônica do produto (obrigatório)
            - url_afiliado: URL de afiliado (opcional)
            - url_imagem: URL da imagem do produto (opcional)
            - preco_original: Preço original (antes do desconto) - opcional
            - fonte: Fonte da oferta (padrão: 'Scraper')
    
    Returns:
        bool: True se a oferta foi adicionada com sucesso, False caso contrário
    """
    # Validação dos campos obrigatórios
    campos_obrigatorios = ['id_produto', 'loja', 'titulo', 'preco', 'url_produto']
    for campo in campos_obrigatorios:
        if campo not in oferta or not oferta[campo]:
            print(f"Erro: Campo obrigatório '{campo}' não fornecido.")
            return False
    
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Verifica se a oferta já existe
        if oferta_ja_existe(oferta['id_produto'], oferta['loja']):
            print(f"Oferta já existe para o produto {oferta['id_produto']} na loja {oferta['loja']}")
            return False
        
        # Gera hash da oferta para deduplicação
        from utils.offer_hash import offer_hash
        offer_hash_value = offer_hash(oferta)
        
        # Verifica se já existe oferta com o mesmo hash
        if oferta_ja_existe_por_hash(offer_hash_value):
            print(f"Oferta duplicada detectada por hash: {offer_hash_value[:16]}...")
            return False
        
        # Prepara os valores para inserção
        campos = [
            'id_produto', 'loja', 'titulo', 'preco', 'preco_original',
            'url_produto', 'url_afiliado', 'url_imagem', 'fonte', 'offer_hash'
        ]
        
        # Define valores padrão
        valores = {
            'preco_original': oferta.get('preco_original', ''),
            'url_afiliado': oferta.get('url_afiliado', ''),
            'url_imagem': oferta.get('url_imagem', ''),
            'fonte': oferta.get('fonte', 'Scraper'),
            'offer_hash': offer_hash_value
        }
        
        # Adiciona os valores fornecidos
        for campo in campos:
            if campo in oferta and oferta[campo]:
                valores[campo] = oferta[campo]
        
        # Monta a query de inserção
        placeholders = ', '.join(['?'] * len(campos))
        campos_str = ', '.join(campos)
        
        cursor.execute(
            f'INSERT INTO ofertas ({campos_str}, data_atualizacao) VALUES ({placeholders}, CURRENT_TIMESTAMP)',
            [valores.get(campo, '') for campo in campos]
        )
        
        conn.commit()
        print(f"Oferta adicionada com sucesso: {oferta['titulo']}")
        return True
        
    except sqlite3.Error as e:
        print(f"Erro ao adicionar oferta: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def oferta_ja_existe_por_url(url: str) -> bool:
    """
    Verifica se uma oferta já existe no banco de dados com base na URL do produto.
    
    Args:
        url: URL do produto a ser verificada
        
    Returns:
        bool: True se uma oferta com esta URL já existe, False caso contrário
    """
    if not url:
        return False
        
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM ofertas WHERE url_produto = ?', (url,))
        return cursor.fetchone() is not None
        
    except sqlite3.Error as e:
        print(f"Erro ao verificar oferta por URL {url}: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def oferta_ja_existe_por_asin(asin: str) -> bool:
    """
    Verifica se uma oferta já existe no banco de dados com base no ASIN (para produtos da Amazon).
    
    Args:
        asin: Amazon Standard Identification Number
        
    Returns:
        bool: True se uma oferta com este ASIN já existe, False caso contrário
    """
    if not asin:
        return False
        
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM ofertas WHERE asin = ?', (asin,))
        return cursor.fetchone() is not None
        
    except sqlite3.Error as e:
        print(f"Erro ao verificar oferta por ASIN {asin}: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def oferta_ja_existe_por_id(id_produto: str, campo_id: str = 'asin') -> bool:
    """
    Verifica se uma oferta já existe no banco de dados com base em um ID de produto.
    
    Esta função é genérica e pode ser usada para verificar a existência de uma oferta
    com base em diferentes tipos de ID (ASIN, ID do AliExpress, etc.).
    
    Args:
        id_produto: ID do produto a ser verificado
        campo_id: Nome da coluna a ser usada na verificação (padrão: 'asin')
        
    Returns:
        bool: True se uma oferta com este ID já existe, False caso contrário
    """
    if not id_produto:
        return False
        
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Usa o campo_id fornecido para fazer a consulta
        query = f'SELECT 1 FROM ofertas WHERE {campo_id} = ?'
        cursor.execute(query, (id_produto,))
        return cursor.fetchone() is not None
        
    except sqlite3.Error as e:
        print(f"Erro ao verificar oferta por ID {id_produto} no campo {campo_id}: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def adicionar_oferta(oferta: Dict[str, Any]) -> bool:
    """
    Adiciona uma nova oferta ao banco de dados.
    
    Args:
        oferta: Dicionário contendo os dados da oferta com as seguintes chaves:
            - url_produto: URL canônica do produto na loja (obrigatório)
            - titulo: Título do produto (obrigatório)
            - preco: Preço atual formatado como string (obrigatório)
            - loja: Nome da loja (ex: 'Magazine Luiza') (obrigatório)
            - fonte: Fonte da oferta (ex: 'Promobit', 'Manual') (obrigatório)
            - preco_original: Preço original (antes do desconto) - opcional
            - url_fonte: URL da oferta na fonte original - opcional
            - imagem_url: URL da imagem do produto - opcional
            - asin: Amazon Standard Identification Number (para produtos da Amazon) - opcional
    
    Returns:
        bool: True se a oferta foi adicionada com sucesso, False caso contrário
    """
    # Validação dos campos obrigatórios
    campos_obrigatorios = ['url_produto', 'titulo', 'preco', 'loja', 'fonte']
    for campo in campos_obrigatorios:
        if campo not in oferta or not oferta[campo]:
            print(f"Erro: Campo obrigatório '{campo}' não fornecido.")
            return False
            
    # Verifica se já existe uma oferta com o mesmo ASIN (para produtos da Amazon)
    if 'asin' in oferta and oferta['asin']:
        if oferta_ja_existe_por_asin(oferta['asin']):
            print(f"Oferta com ASIN {oferta['asin']} já existe no banco de dados.")
            return False
    
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Verifica se a oferta já existe
        if oferta_ja_existe(oferta['url_produto']):
            print(f"Oferta já existe: {oferta['titulo']}")
            return False
            
        # Prepara os valores para inserção
        valores = [
            oferta['url_produto'],
            oferta['titulo'],
            oferta['preco'],
            oferta.get('preco_original'),
            oferta['loja'],
            oferta['fonte'],
            oferta.get('url_fonte'),
            oferta.get('imagem_url'),
            oferta.get('asin')
        ]
        
        # Insere a nova oferta
        cursor.execute('''
        INSERT INTO ofertas (
            url_produto, titulo, preco, preco_original, 
            loja, fonte, url_fonte, imagem_url, asin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', valores)
        
        conn.commit()
        print(f"✅ Oferta adicionada: {oferta['titulo']}")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar oferta: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def adicionar_oferta_manual(url: str, titulo: str, preco: str) -> bool:
    """
    Função de compatibilidade para adicionar ofertas manualmente.
    Mantida para compatibilidade com o código existente.
    
    Args:
        url: URL do produto
        titulo: Título do produto
        preco: Preço formatado como string
        
    Returns:
        bool: True se a oferta foi adicionada com sucesso, False caso contrário
    """
    oferta = {
        'url_produto': url,
        'titulo': titulo,
        'preco': preco,
        'loja': extrair_dominio_loja(url),
        'fonte': 'Manual',
        'url_fonte': url
    }
    return adicionar_oferta(oferta)

def obter_ultimas_ofertas(limite: int = 10) -> List[Dict[str, Any]]:
    """
    Obtém as últimas ofertas adicionadas ao banco de dados.
    
    Args:
        limite: Número máximo de ofertas a retornar
        
    Returns:
        List[Dict]: Lista de dicionários contendo as ofertas
    """
    try:
        conn = sqlite3.connect(config.DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ofertas 
            ORDER BY data_postagem DESC 
            LIMIT ?
        ''', (limite,))
        
        # Converte as linhas para dicionários
        ofertas = [dict(row) for row in cursor.fetchall()]
        return ofertas
        
    except sqlite3.Error as e:
        print(f"Erro ao obter últimas ofertas: {e}")
        return []
        
    finally:
        if 'conn' in locals():
            conn.close()
