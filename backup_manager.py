"""
Sistema de Backup Automático do Banco de Dados
Módulo responsável por criar backups automáticos e gerenciar a rotação de arquivos antigos.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Configuração do logger
logger = logging.getLogger(__name__)

# Configurações do backup
BACKUP_DIR = "db_backups"
MAX_BACKUP_AGE_DAYS = 7  # Manter apenas backups dos últimos 7 dias
DB_NAME = "ofertas.db"  # Nome do banco de dados principal

def criar_pasta_backup() -> bool:
    """
    Cria a pasta de backup se ela não existir.
    
    Returns:
        bool: True se a pasta foi criada ou já existe, False em caso de erro
    """
    try:
        backup_path = Path(BACKUP_DIR)
        if not backup_path.exists():
            backup_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Pasta de backup criada: {backup_path.absolute()}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar pasta de backup: {e}")
        return False

def gerar_nome_backup() -> str:
    """
    Gera um nome único para o arquivo de backup baseado na data e hora atual.
    
    Returns:
        str: Nome do arquivo de backup (ex: ofertas_backup_2025-01-27_15-30-45.db)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"ofertas_backup_{timestamp}.db"

def limpar_backups_antigos() -> int:
    """
    Remove backups antigos baseado na configuração MAX_BACKUP_AGE_DAYS.
    
    Returns:
        int: Número de arquivos removidos
    """
    try:
        backup_path = Path(BACKUP_DIR)
        if not backup_path.exists():
            return 0
            
        cutoff_date = datetime.now() - timedelta(days=MAX_BACKUP_AGE_DAYS)
        arquivos_removidos = 0
        
        for arquivo in backup_path.glob("ofertas_backup_*.db"):
            try:
                # Obtém a data de modificação do arquivo
                mtime = datetime.fromtimestamp(arquivo.stat().st_mtime)
                
                if mtime < cutoff_date:
                    arquivo.unlink()
                    arquivos_removidos += 1
                    logger.info(f"Backup antigo removido: {arquivo.name}")
                    
            except Exception as e:
                logger.warning(f"Erro ao processar arquivo {arquivo.name}: {e}")
                
        if arquivos_removidos > 0:
            logger.info(f"Removidos {arquivos_removidos} backups antigos")
            
        return arquivos_removidos
        
    except Exception as e:
        logger.error(f"Erro ao limpar backups antigos: {e}")
        return 0

def fazer_backup_db() -> bool:
    """
    Função principal que executa o backup completo do banco de dados.
    
    Returns:
        bool: True se o backup foi bem-sucedido, False caso contrário
    """
    try:
        # Verifica se o banco de dados existe
        if not os.path.exists(DB_NAME):
            logger.error(f"Banco de dados não encontrado: {DB_NAME}")
            return False
            
        # Cria a pasta de backup se necessário
        if not criar_pasta_backup():
            return False
            
        # Gera nome único para o backup
        nome_backup = gerar_nome_backup()
        caminho_backup = os.path.join(BACKUP_DIR, nome_backup)
        
        # Executa a cópia do banco de dados
        shutil.copy2(DB_NAME, caminho_backup)
        
        # Verifica se o backup foi criado com sucesso
        if os.path.exists(caminho_backup):
            tamanho_original = os.path.getsize(DB_NAME)
            tamanho_backup = os.path.getsize(caminho_backup)
            
            if tamanho_original == tamanho_backup:
                logger.info(f"Backup criado com sucesso: {nome_backup} ({tamanho_backup} bytes)")
                
                # Limpa backups antigos
                arquivos_removidos = limpar_backups_antigos()
                
                # Log final
                logger.info(f"Backup concluído. Arquivo: {nome_backup}, Backups antigos removidos: {arquivos_removidos}")
                return True
            else:
                logger.error(f"Backup corrompido: tamanhos diferentes (original: {tamanho_original}, backup: {tamanho_backup})")
                # Remove o backup corrompido
                if os.path.exists(caminho_backup):
                    os.remove(caminho_backup)
                return False
        else:
            logger.error(f"Falha ao criar backup: arquivo não encontrado em {caminho_backup}")
            return False
            
    except Exception as e:
        logger.exception(f"Erro crítico durante o backup: {e}")
        return False

def listar_backups() -> list:
    """
    Lista todos os backups disponíveis com informações de tamanho e data.
    
    Returns:
        list: Lista de dicionários com informações dos backups
    """
    try:
        backup_path = Path(BACKUP_DIR)
        if not backup_path.exists():
            return []
            
        backups = []
        for arquivo in sorted(backup_path.glob("ofertas_backup_*.db"), reverse=True):
            try:
                stat = arquivo.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                tamanho = stat.st_size
                
                backups.append({
                    'nome': arquivo.name,
                    'tamanho': tamanho,
                    'data_criacao': mtime,
                    'idade_dias': (datetime.now() - mtime).days
                })
                
            except Exception as e:
                logger.warning(f"Erro ao processar arquivo {arquivo.name}: {e}")
                
        return backups
        
    except Exception as e:
        logger.error(f"Erro ao listar backups: {e}")
        return []

def obter_estatisticas_backup() -> dict:
    """
    Obtém estatísticas sobre o sistema de backup.
    
    Returns:
        dict: Dicionário com estatísticas do backup
    """
    try:
        backup_path = Path(BACKUP_DIR)
        if not backup_path.exists():
            return {
                'pasta_existe': False,
                'total_backups': 0,
                'tamanho_total': 0,
                'backup_mais_recente': None,
                'backup_mais_antigo': None
            }
            
        backups = listar_backups()
        
        if not backups:
            return {
                'pasta_existe': True,
                'total_backups': 0,
                'tamanho_total': 0,
                'backup_mais_recente': None,
                'backup_mais_antigo': None
            }
            
        tamanho_total = sum(b['tamanho'] for b in backups)
        backup_mais_recente = backups[0]['data_criacao'] if backups else None
        backup_mais_antigo = backups[-1]['data_criacao'] if backups else None
        
        return {
            'pasta_existe': True,
            'total_backups': len(backups),
            'tamanho_total': tamanho_total,
            'backup_mais_recente': backup_mais_recente,
            'backup_mais_antigo': backup_mais_antigo,
            'tamanho_medio': tamanho_total / len(backups) if backups else 0
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de backup: {e}")
        return {
            'erro': str(e)
        }

if __name__ == "__main__":
    # Teste do módulo
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Testando módulo de backup...")
    
    # Testa criação de pasta
    print(f"Pasta de backup criada: {criar_pasta_backup()}")
    
    # Testa geração de nome
    nome = gerar_nome_backup()
    print(f"Nome do backup gerado: {nome}")
    
    # Testa estatísticas
    stats = obter_estatisticas_backup()
    print(f"Estatísticas: {stats}")
    
    # Testa listagem
    backups = listar_backups()
    print(f"Backups encontrados: {len(backups)}")
    
    print("Teste concluído!")
