"""
Script orquestrador para busca e publicação de ofertas.

Este script coordena a busca de ofertas em diferentes fontes (Magazine Luiza, Promobit, etc.),
verifica duplicatas, gera links de afiliado e publica as ofertas no canal do Telegram.
"""
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# Importações dos módulos personalizados
try:
    import config
    import database
    from magalu_scraper import buscar_ofertas_magalu
    from promobit_scraper import buscar_ofertas_promobit
    from affiliate import gerar_link_afiliado
    from telegram_poster import publicar_oferta_automatica
    
    # Configuração de disponibilidade de módulos
    PROMOBIT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {e}")
    raise

# Configurações
INTERVALO_ENTRE_EXECUCOES = 3600  # 1 hora
MAX_OFERTAS_POR_EXECUCAO = 5      # Número máximo de ofertas por execução
INTERVALO_ENTRE_PUBLICACOES = 60  # 60 segundos entre publicações

# Cria diretório de logs se não existir
os.makedirs('logs', exist_ok=True)

class ScraperOrchestrator:
    """Classe para orquestrar a busca e publicação de ofertas."""
    
    def __init__(self):
        self.ultima_execucao = datetime.now()
        self.sessao = None
        self.total_ofertas_publicadas = 0
        self.total_ofertas_ignoradas = 0
    
    async def inicializar(self):
        """Inicializa os recursos necessários."""
        logger.info("🚀 Inicializando ScraperOrchestrator...")
        
        # Configura o banco de dados
        try:
            database.setup_database()
            logger.info("✅ Banco de dados configurado")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar banco de dados: {e}")
            raise
        
        logger.info("✅ Inicialização concluída")
    
    async def finalizar(self):
        """Libera os recursos utilizados."""
        logger.info("🔒 Finalizando ScraperOrchestrator...")
        if self.sessao:
            await self.sessao.close()
            self.sessao = None
        logger.info("✅ Recursos liberados")
    
    async def buscar_todas_as_ofertas(self) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Busca ofertas de todas as fontes configuradas.
        
        Returns:
            Tuple[List[Dict], Dict]: Lista de ofertas e estatísticas
        """
        logger.info("🔍 Iniciando busca por ofertas...")
        
        # Dicionário para estatísticas
        stats = {
            'magalu': 0,
            'promobit': 0,
            'total': 0,
            'erros': 0
        }
        
        # Lista para armazenar todas as ofertas encontradas
        todas_as_ofertas = []
        
        try:
            # 1. Busca ofertas do Magazine Luiza
            logger.info("🔄 Buscando ofertas no Magazine Luiza...")
            try:
                ofertas_magalu = await asyncio.to_thread(buscar_ofertas_magalu, paginas=2)
                stats['magalu'] = len(ofertas_magalu)
                todas_as_ofertas.extend(ofertas_magalu)
                logger.info(f"✅ Encontradas {len(ofertas_magalu)} ofertas no Magazine Luiza")
                await asyncio.sleep(5)  # Delay para não sobrecarregar os servidores
            except Exception as e:
                logger.error(f"❌ Erro ao buscar ofertas do Magazine Luiza: {e}", exc_info=True)
                stats['erros'] += 1
            
            # 2. Busca ofertas do Promobit (se disponível)
            if PROMOBIT_AVAILABLE:
                logger.info("🔄 Buscando ofertas no Promobit...")
                ofertas_promobit = await buscar_ofertas_promobit(
                    self.sessao, 
                    max_paginas=2  # Limita a 2 páginas para não sobrecarregar
                )
                logger.info(f"✅ Encontradas {len(ofertas_promobit)} ofertas no Promobit")
                todas_as_ofertas.extend(ofertas_promobit)
                await asyncio.sleep(5)  # Delay entre requisições
            
            # 3. Busca ofertas do Pelando (se disponível)
            if PELANDO_AVAILABLE:
                logger.info("🔄 Buscando ofertas no Pelando...")
                ofertas_pelando = await buscar_ofertas_pelando(
                    self.sessao,
                    max_paginas=1  # Limita a 1 página para não sobrecarregar
                )
                logger.info(f"✅ Encontradas {len(ofertas_pelando)} ofertas no Pelando")
                todas_as_ofertas.extend(ofertas_pelando)
            
            # Filtra ofertas duplicadas (mesma URL de produto)
            ofertas_unicas = {}
            for oferta in todas_as_ofertas:
                url = oferta.get('url_produto')
                if url and url not in ofertas_unicas:
                    ofertas_unicas[url] = oferta
            
            logger.info(f"📊 Total de ofertas únicas encontradas: {len(ofertas_unicas)}")
            return list(ofertas_unicas.values())
            
        except Exception as e:
            logger.error(f" Erro inesperado ao buscar ofertas: {e}", exc_info=True)
            stats['erros'] += 1
            return [], stats
    
    async def processar_e_publicar_ofertas(self, ofertas: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Processa as ofertas encontradas e as publica no canal.
        
        Args:
            ofertas: Lista de ofertas a serem processadas
            
        Returns:
            Dict: Estatísticas do processamento
        """
        stats = {
            'total_processadas': 0,
            'publicadas': 0,
            'ignoradas': 0,
            'erros': 0
        }
        
        if not ofertas:
            logger.info(" Nenhuma oferta para processar")
            return stats
        
        logger.info(f" Processando {len(ofertas)} ofertas...")
        
        # Ordena as ofertas por desconto (maiores descontos primeiro)
        ofertas_ordenadas = sorted(
            ofertas,
            key=lambda x: (
                float(x.get('desconto', '0').replace('%', '')) 
                if x.get('desconto') and isinstance(x.get('desconto'), str) 
                else 0
            ),
            reverse=True
        )
        
        # Limita o número de ofertas a serem publicadas
        ofertas_publicar = ofertas_ordenadas[:MAX_OFERTAS_POR_EXECUCAO]
        
        for oferta in ofertas_publicar:
            stats['total_processadas'] += 1
            
            try:
                # Verifica se a oferta já foi publicada
                if database.oferta_ja_existe(oferta['url_produto']):
                    logger.debug(f" Oferta já publicada: {oferta.get('titulo', 'Sem título')}")
                    stats['ignoradas'] += 1
                    continue
                
                # Gera o link de afiliado
                url_afiliado = gerar_link_afiliado(oferta['url_produto'])
                
                # Prepara os dados da oferta para publicação
                dados_publicacao = {
                    'titulo': oferta.get('titulo', 'Oferta sem título'),
                    'preco_atual': oferta.get('preco', 'Preço não disponível'),
                    'preco_original': oferta.get('preco_original'),
                    'desconto': oferta.get('desconto'),
                    'url_afiliado': url_afiliado,
                    'imagem_url': oferta.get('imagem_url'),
                    'loja': oferta.get('loja', 'Desconhecida'),
                    'fonte': oferta.get('fonte', 'Desconhecida')
                }
                
                # Publica a oferta
                publicada = await publicar_oferta_automatica(dados_publicacao)
                
                if publicada:
                    # Salva a oferta no banco de dados
                    oferta_db = {
                        'url_produto': oferta['url_produto'],
                        'titulo': oferta.get('titulo', 'Oferta sem título'),
                        'preco': oferta.get('preco', 'Preço não disponível'),
                        'preco_original': oferta.get('preco_original'),
                        'loja': oferta.get('loja', 'Desconhecida'),
                        'fonte': oferta.get('fonte', 'Scraper'),
                        'imagem_url': oferta.get('imagem_url'),
                        'asin': oferta.get('asin')
                    }
                    
                    try:
                        database.adicionar_oferta(oferta_db)
                        logger.info(f" Oferta publicada: {oferta.get('titulo', 'Sem título')}")
                        stats['publicadas'] += 1
                        
                        # Aguarda um tempo entre publicações
                        await asyncio.sleep(INTERVALO_ENTRE_PUBLICACOES)
                        
                    except Exception as db_error:
                        logger.error(f" Erro ao salvar oferta no banco: {db_error}", exc_info=True)
                        stats['erros'] += 1
                else:
                    logger.error(f" Falha ao publicar oferta: {oferta.get('titulo', 'Sem título')}")
                    stats['erros'] += 1
                
            except Exception as e:
                logger.error(f" Erro ao processar oferta: {e}", exc_info=True)
                stats['erros'] += 1
                continue
                
        return stats
    
    async def executar_ciclo(self) -> Dict[str, int]:
        """
        Executa um ciclo completo de busca e publicação de ofertas.
        
        Returns:
            Dict: Estatísticas do ciclo
        """
        logger.info("🔄 Iniciando ciclo de busca e publicação de ofertas...")
        
        stats = {
            'ofertas_encontradas': 0,
            'ofertas_publicadas': 0,
            'ofertas_ignoradas': 0,
            'erros': 0,
            'tempo_execucao': 0
        }
        
        start_time = time.time()
        
        try:
            # Busca ofertas de todas as fontes
            ofertas, busca_stats = await self.buscar_todas_as_ofertas()
            stats['ofertas_encontradas'] = busca_stats.get('total', 0)
            stats['erros'] += busca_stats.get('erros', 0)
            
            if not ofertas:
                logger.info("ℹ️ Nenhuma oferta encontrada")
                return stats
            
            # Processa e publica as ofertas
            processamento_stats = await self.processar_e_publicar_ofertas(ofertas)
            
            # Atualiza estatísticas
            stats['ofertas_publicadas'] = processamento_stats.get('publicadas', 0)
            stats['ofertas_ignoradas'] = processamento_stats.get('ignoradas', 0)
            stats['erros'] += processamento_stats.get('erros', 0)
            
            logger.info("✅ Ciclo de busca e publicação concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro durante o ciclo de busca: {e}", exc_info=True)
            stats['erros'] += 1
        finally:
            # Atualiza o timestamp da última execução e calcula o tempo total
            self.ultima_execucao = datetime.now()
            stats['tempo_execucao'] = int(time.time() - start_time)
            
            # Log das estatísticas
            logger.info("📊 Estatísticas do ciclo:" +
                       f"\n- Ofertas encontradas: {stats['ofertas_encontradas']}" +
                       f"\n- Ofertas publicadas: {stats['ofertas_publicadas']}" +
                       f"\n- Ofertas ignoradas: {stats['ofertas_ignoradas']}" +
                       f"\n- Erros: {stats['erros']}" +
                       f"\n- Tempo de execução: {stats['tempo_execucao']} segundos")
        
        return stats
    
    async def executar(self):
        """
        Executa o orquestrador em loop contínuo.
        
        Este método fica em loop, executando ciclos de busca e publicação
        com um intervalo entre eles.
        """
        logger.info("🚀 Iniciando orquestrador em modo contínuo...")
        
        try:
            while True:
                # Executa um ciclo completo
                stats = await self.executar_ciclo()
                
                # Calcula o tempo até a próxima execução
                tempo_ate_proxima = max(0, INTERVALO_ENTRE_EXECUCOES - stats['tempo_execucao'])
                
                if tempo_ate_proxima > 0:
                    minutos = int(tempo_ate_proxima / 60)
                    segundos = int(tempo_ate_proxima % 60)
                    logger.info(f"⏳ Próxima execução em {minutos} minutos e {segundos} segundos...")
                    await asyncio.sleep(tempo_ate_proxima)
                
        except asyncio.CancelledError:
            logger.info("👋 Recebido sinal de cancelamento. Encerrando...")
        except Exception as e:
            logger.error(f"❌ Erro fatal no orquestrador: {e}", exc_info=True)
            raise

async def main():
    """Função principal para execução direta do script."""
    # Cria o orquestrador
    orquestrador = ScraperOrchestrator()
    
    try:
        # Inicializa o orquestrador
        await orquestrador.inicializar()
        
        # Executa o orquestrador em modo contínuo
        await orquestrador.executar()
        
    except KeyboardInterrupt:
        logger.info("👋 Encerrando o orquestrador...")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        return 1
    finally:
        # Finaliza o orquestrador
        await orquestrador.finalizar()
    
    return 0

if __name__ == "__main__":
    # Configura o nível de log para DEBUG se executado diretamente
    logger.setLevel(logging.DEBUG)
    
    # Executa o script e sai com o código de status apropriado
    exit_code = asyncio.run(main())
    exit(exit_code)
