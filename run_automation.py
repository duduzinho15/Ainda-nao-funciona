"""
Sistema Principal de Automação do Garimpeiro Geek
Integra scraping, filtros, conversão de afiliados e publicação no Telegram
"""
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

# Importa o sistema de logging centralizado
from logger_config import (
    get_logger, log_info, log_error, log_warning, 
    log_new_product, log_duplicate_product, log_telegram_publication,
    log_automation_cycle, log_affiliate_conversion, log_database_operation
)

# Importa os módulos do sistema
from scraper_orchestrator import ScraperOrchestrator
from database import Database
from affiliate import converter_para_afiliado
from telegram_poster import TelegramPoster
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

class GarimpeiroAutomation:
    """Sistema principal de automação do Garimpeiro Geek"""
    
    def __init__(self):
        self.logger = get_logger("automation")
        self.orchestrator = ScraperOrchestrator(use_stealth=True, max_workers=3)
        self.database = Database()
        self.telegram_poster = TelegramPoster(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
        self.cycle_count = 0
        
        log_info("AUTOMAÇÃO", "Sistema de automação inicializado")
    
    async def executar_ciclo_completo(self, 
                                    min_desconto: int = 0,
                                    max_preco: float = None,
                                    categoria_filtro: str = None) -> Dict:
        """Executa um ciclo completo de automação"""
        cycle_start = time.time()
        self.cycle_count += 1
        
        log_info("CICLO", f"Iniciando ciclo de automação #{self.cycle_count}")
        
        try:
            # FASE 1: Coleta de dados
            log_info("CICLO", "Fase 1: Iniciando coleta de dados")
            ofertas = await self.orchestrator.run_complete_scraping(
                use_stealth=True,
                use_advanced=True,
                min_desconto=min_desconto,
                max_preco=max_preco,
                categoria_filtro=categoria_filtro
            )
            
            if not ofertas:
                log_warning("CICLO", "Nenhuma oferta encontrada no ciclo atual")
                return {
                    'cycle_number': self.cycle_count,
                    'total_products': 0,
                    'new_products': 0,
                    'published': 0,
                    'duration': time.time() - cycle_start
                }
            
            log_info("CICLO", f"Fase 1 concluída: {len(ofertas)} ofertas coletadas")
            
            # FASE 2: Análise de duplicatas e novos produtos
            log_info("CICLO", "Fase 2: Analisando duplicatas e novos produtos")
            novos_produtos = []
            duplicatas = 0
            
            for oferta in ofertas:
                try:
                    # Verifica se já existe no banco
                    if self.database.oferta_ja_existe(oferta['url_produto']):
                        log_duplicate_product(oferta['titulo'], oferta['loja'])
                        duplicatas += 1
                        continue
                    
                    # Produto novo
                    log_new_product(oferta['titulo'], oferta['loja'])
                    novos_produtos.append(oferta)
                    
                except Exception as e:
                    log_error("ANÁLISE DUPLICATAS", e, f"Produto: {oferta.get('titulo', 'N/A')}")
                    continue
            
            log_info("CICLO", f"Fase 2 concluída: {len(novos_produtos)} novos produtos, {duplicatas} duplicatas")
            
            # FASE 3: Conversão de links de afiliado
            log_info("CICLO", "Fase 3: Convertendo links de afiliado")
            produtos_com_afiliado = []
            
            for produto in novos_produtos:
                try:
                    affiliate_url = converter_para_afiliado(produto['url_produto'], produto['loja'])
                    if affiliate_url:
                        produto['url_afiliado'] = affiliate_url
                        log_affiliate_conversion(produto['url_produto'], affiliate_url)
                        produtos_com_afiliado.append(produto)
                    else:
                        log_warning("AFILIADO", f"Falha na conversão para: {produto['titulo'][:50]}...")
                        # Mantém o produto mesmo sem afiliado
                        produtos_com_afiliado.append(produto)
                        
                except Exception as e:
                    log_error("CONVERSÃO AFILIADO", e, f"Produto: {produto.get('titulo', 'N/A')}")
                    # Mantém o produto mesmo com erro na conversão
                    produtos_com_afiliado.append(produto)
            
            log_info("CICLO", f"Fase 3 concluída: {len(produtos_com_afiliado)} produtos com links de afiliado")
            
            # FASE 4: Publicação no Telegram
            log_info("CICLO", "Fase 4: Publicando ofertas no Telegram")
            publicados = 0
            falhas_publicacao = 0
            
            for produto in produtos_com_afiliado:
                try:
                    # Prepara mensagem para o Telegram
                    mensagem = self._criar_mensagem_telegram(produto)
                    
                    # Publica no canal
                    success = await self.telegram_poster.publicar_oferta(mensagem)
                    
                    if success:
                        publicados += 1
                        log_telegram_publication(produto['titulo'], True)
                        
                        # Salva no banco após publicação bem-sucedida
                        try:
                            self.database.adicionar_oferta(produto)
                            log_database_operation("INSERÇÃO", produto['titulo'], True)
                        except Exception as e:
                            log_error("BANCO DADOS", e, f"Falha ao salvar produto: {produto['titulo'][:50]}...")
                    else:
                        falhas_publicacao += 1
                        log_telegram_publication(produto['titulo'], False, "Falha na publicação")
                        
                except Exception as e:
                    falhas_publicacao += 1
                    log_error("PUBLICAÇÃO TELEGRAM", e, f"Produto: {produto.get('titulo', 'N/A')}")
                    continue
            
            log_info("CICLO", f"Fase 4 concluída: {publicados} publicados, {falhas_publicacao} falhas")
            
            # FASE 5: Resumo do ciclo
            cycle_duration = time.time() - cycle_start
            log_automation_cycle(self.cycle_count, len(ofertas), len(novos_produtos), publicados)
            
            log_info("CICLO", f"Ciclo #{self.cycle_count} concluído em {cycle_duration:.2f}s")
            
            return {
                'cycle_number': self.cycle_count,
                'total_products': len(ofertas),
                'new_products': len(novos_produtos),
                'duplicates': duplicatas,
                'published': publicados,
                'publication_failures': falhas_publicacao,
                'duration': cycle_duration
            }
            
        except Exception as e:
            cycle_duration = time.time() - cycle_start
            log_error("CICLO COMPLETO", e, f"Ciclo #{self.cycle_count} falhou após {cycle_duration:.2f}s")
            raise
    
    def _criar_mensagem_telegram(self, produto: Dict) -> str:
        """Cria mensagem formatada para o Telegram"""
        try:
            titulo = produto.get('titulo', 'Produto sem título')
            preco = produto.get('preco', 'Preço não informado')
            loja = produto.get('loja', 'Loja não informada')
            desconto = produto.get('desconto')
            url = produto.get('url_afiliado', produto.get('url_produto', '#'))
            
            # Formata a mensagem
            mensagem = f"🛍️ **{titulo}**\n\n"
            mensagem += f"💰 **Preço:** R$ {preco}\n"
            
            if desconto:
                mensagem += f"🏷️ **Desconto:** {desconto}% OFF\n"
            
            mensagem += f"🏪 **Loja:** {loja}\n\n"
            mensagem += f"🔗 [Ver Oferta]({url})\n\n"
            mensagem += f"#oferta #tecnologia #{loja.lower().replace(' ', '')}"
            
            return mensagem
            
        except Exception as e:
            log_error("MENSAGEM TELEGRAM", e, f"Produto: {produto.get('titulo', 'N/A')}")
            return f"🛍️ **{produto.get('titulo', 'Produto')}**\n\n💰 **Preço:** R$ {produto.get('preco', 'N/A')}\n🏪 **Loja:** {produto.get('loja', 'N/A')}"
    
    async def executar_automaticamente(self, 
                                     intervalo_segundos: int = 3600,
                                     max_ciclos: int = None,
                                     min_desconto: int = 0,
                                     max_preco: float = None,
                                     categoria_filtro: str = None):
        """Executa automação em loop contínuo"""
        log_info("AUTOMAÇÃO", f"Iniciando execução automática - Intervalo: {intervalo_segundos}s")
        
        ciclo_atual = 0
        
        try:
            while True:
                if max_ciclos and ciclo_atual >= max_ciclos:
                    log_info("AUTOMAÇÃO", f"Limite de {max_ciclos} ciclos atingido")
                    break
                
                ciclo_atual += 1
                log_info("AUTOMAÇÃO", f"Executando ciclo automático #{ciclo_atual}")
                
                try:
                    resultado = await self.executar_ciclo_completo(
                        min_desconto=min_desconto,
                        max_preco=max_preco,
                        categoria_filtro=categoria_filtro
                    )
                    
                    log_info("AUTOMAÇÃO", f"Ciclo #{ciclo_atual} concluído: {resultado['published']} produtos publicados")
                    
                except Exception as e:
                    log_error("AUTOMAÇÃO AUTOMÁTICA", e, f"Ciclo #{ciclo_atual} falhou")
                    continue
                
                # Aguarda próximo ciclo
                if ciclo_atual < (max_ciclos or float('inf')):
                    log_info("AUTOMAÇÃO", f"Aguardando {intervalo_segundos}s para próximo ciclo...")
                    await asyncio.sleep(intervalo_segundos)
                
        except KeyboardInterrupt:
            log_info("AUTOMAÇÃO", "Execução automática interrompida pelo usuário")
        except Exception as e:
            log_error("AUTOMAÇÃO AUTOMÁTICA", e, "Erro fatal na execução automática")
            raise

async def main():
    """Função principal para teste"""
    automation = GarimpeiroAutomation()
    
    print("🚀 SISTEMA DE AUTOMAÇÃO GARIMPEIRO GEEK")
    print("=" * 50)
    
    try:
        # Executa um ciclo de teste
        resultado = await automation.executar_ciclo_completo(
            min_desconto=0,
            max_preco=5000.0,
            categoria_filtro=None
        )
        
        print(f"\n✅ CICLO DE TESTE CONCLUÍDO!")
        print(f"📊 Resumo:")
        print(f"   🔄 Ciclo: #{resultado['cycle_number']}")
        print(f"   📦 Total de produtos: {resultado['total_products']}")
        print(f"   🆕 Novos produtos: {resultado['new_products']}")
        print(f"   📱 Publicados: {resultado['published']}")
        print(f"   ⏱️ Duração: {resultado['duration']:.2f}s")
        
        if resultado['publication_failures'] > 0:
            print(f"   ❌ Falhas na publicação: {resultado['publication_failures']}")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        log_error("TESTE PRINCIPAL", e, "Teste da função main falhou")

if __name__ == "__main__":
    asyncio.run(main())

