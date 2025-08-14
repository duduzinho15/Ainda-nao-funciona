#!/usr/bin/env python3
"""
Script de teste para a integração com a API da Shopee.

Este script testa todas as funcionalidades da API da Shopee implementada.
"""

import sys
import os
import logging
import asyncio
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_shopee_api_import():
    """Testa se o módulo da API da Shopee pode ser importado."""
    try:
        from shopee_api_integration import ShopeeAPIIntegration, verificar_ofertas_shopee
        logger.info("✅ Módulo da API da Shopee importado com sucesso!")
        return True
    except ImportError as e:
        logger.error(f"❌ Erro ao importar módulo da API da Shopee: {e}")
        return False

def test_shopee_api_initialization():
    """Testa a inicialização da API da Shopee."""
    try:
        from shopee_api_integration import ShopeeAPIIntegration
        
        shopee_api = ShopeeAPIIntegration()
        logger.info("✅ API da Shopee inicializada com sucesso!")
        
        # Verifica se as configurações estão disponíveis
        if shopee_api.api_available:
            logger.info("✅ Configurações da API da Shopee estão disponíveis")
        else:
            logger.warning("⚠️ Configurações da API da Shopee não estão disponíveis")
            logger.info("ℹ️ Configure as variáveis de ambiente ou crie um arquivo .env")
        
        return shopee_api
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar API da Shopee: {e}")
        return None

def test_shopee_connection(shopee_api):
    """Testa a conexão com a API da Shopee."""
    if not shopee_api:
        logger.error("❌ API da Shopee não inicializada")
        return False
    
    try:
        logger.info("🧪 Testando conexão com a API da Shopee...")
        
        # Testa conexão básica
        connection_success = shopee_api.test_connection()
        
        if connection_success:
            logger.info("✅ Conexão com a API da Shopee estabelecida!")
            return True
        else:
            logger.warning("⚠️ Falha na conexão com a API da Shopee")
            logger.info("ℹ️ Verifique suas credenciais e configurações")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao testar conexão: {e}")
        return False

def test_shopee_search_functionality(shopee_api):
    """Testa as funcionalidades de busca da API da Shopee."""
    if not shopee_api:
        logger.error("❌ API da Shopee não inicializada")
        return False
    
    try:
        logger.info("🔍 Testando funcionalidades de busca...")
        
        # Testa busca por palavra-chave
        logger.info("Testando busca por palavra-chave 'smartphone'...")
        smartphones = shopee_api.search_products("smartphone", limit=3)
        
        if smartphones:
            logger.info(f"✅ Encontrados {len(smartphones)} smartphones")
            for i, produto in enumerate(smartphones[:2], 1):
                logger.info(f"   {i}. {produto['titulo']} - R$ {produto['preco']}")
        else:
            logger.warning("⚠️ Nenhum smartphone encontrado")
        
        # Testa busca por categoria
        logger.info("Testando busca por categoria 'Computadores e Acessórios'...")
        computadores = shopee_api.get_category_products(11001205, limit=3)
        
        if computadores:
            logger.info(f"✅ Encontrados {len(computadores)} produtos na categoria")
            for i, produto in enumerate(computadores[:2], 1):
                logger.info(f"   {i}. {produto['titulo']} - R$ {produto['preco']}")
        else:
            logger.warning("⚠️ Nenhum produto encontrado na categoria")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar funcionalidades de busca: {e}")
        return False

def test_shopee_general_search(shopee_api):
    """Testa a busca geral de ofertas da Shopee."""
    if not shopee_api:
        logger.error("❌ API da Shopee não inicializada")
        return False
    
    try:
        logger.info("🎯 Testando busca geral de ofertas...")
        
        # Busca ofertas gerais
        ofertas = shopee_api.buscar_ofertas_gerais(limit=5)
        
        if ofertas:
            logger.info(f"✅ Encontradas {len(ofertas)} ofertas gerais!")
            
            # Exibe detalhes das ofertas
            for i, oferta in enumerate(ofertas, 1):
                logger.info(f"\n{i}. {oferta['titulo']}")
                logger.info(f"   Preço: R$ {oferta['preco']}")
                if oferta.get('preco_original'):
                    logger.info(f"   Preço Original: R$ {oferta['preco_original']}")
                logger.info(f"   Desconto: {oferta['desconto']}%")
                logger.info(f"   Loja: {oferta['loja']}")
                logger.info(f"   Categoria: {oferta['categoria']}")
                if oferta.get('rating'):
                    logger.info(f"   Avaliação: {oferta['rating']}/5")
                if oferta.get('vendas'):
                    logger.info(f"   Vendas: {oferta['vendas']}")
                logger.info(f"   URL: {oferta['url_produto']}")
        else:
            logger.warning("⚠️ Nenhuma oferta encontrada na busca geral")
        
        return len(ofertas) > 0
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar busca geral: {e}")
        return False

def test_shopee_function_wrapper():
    """Testa a função de conveniência verificar_ofertas_shopee."""
    try:
        logger.info("🔄 Testando função de conveniência verificar_ofertas_shopee...")
        
        from shopee_api_integration import verificar_ofertas_shopee
        
        ofertas = verificar_ofertas_shopee(limit=3)
        
        if ofertas:
            logger.info(f"✅ Função de conveniência funcionando! Encontradas {len(ofertas)} ofertas")
            return True
        else:
            logger.warning("⚠️ Função de conveniência não retornou ofertas")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao testar função de conveniência: {e}")
        return False

def test_shopee_data_format():
    """Testa se os dados retornados estão no formato correto."""
    try:
        logger.info("📊 Testando formato dos dados...")
        
        from shopee_api_integration import ShopeeAPIIntegration
        
        shopee_api = ShopeeAPIIntegration()
        
        # Busca alguns produtos para testar o formato
        produtos = shopee_api.search_products("notebook", limit=2)
        
        if not produtos:
            logger.warning("⚠️ Nenhum produto para testar formato")
            return False
        
        # Verifica campos obrigatórios
        campos_obrigatorios = [
            'titulo', 'preco', 'desconto', 'url_produto', 
            'url_afiliado', 'loja', 'categoria'
        ]
        
        for i, produto in enumerate(produtos):
            logger.info(f"Verificando produto {i+1}: {produto['titulo']}")
            
            for campo in campos_obrigatorios:
                if campo not in produto:
                    logger.error(f"❌ Campo obrigatório '{campo}' não encontrado")
                    return False
                else:
                    logger.info(f"   ✅ {campo}: {produto[campo]}")
        
        logger.info("✅ Formato dos dados está correto!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar formato dos dados: {e}")
        return False

def run_all_tests():
    """Executa todos os testes da API da Shopee."""
    logger.info("🚀 Iniciando testes da API da Shopee...")
    logger.info("=" * 50)
    
    results = {}
    
    # Teste 1: Importação
    logger.info("\n📦 Teste 1: Importação do módulo")
    results['import'] = test_shopee_api_import()
    
    # Teste 2: Inicialização
    logger.info("\n🔧 Teste 2: Inicialização da API")
    shopee_api = test_shopee_api_initialization()
    results['initialization'] = shopee_api is not None
    
    # Teste 3: Conexão (apenas se inicialização foi bem-sucedida)
    if shopee_api:
        logger.info("\n🔌 Teste 3: Teste de conexão")
        results['connection'] = test_shopee_connection(shopee_api)
        
        # Teste 4: Funcionalidades de busca (apenas se conexão foi bem-sucedida)
        if results['connection']:
            logger.info("\n🔍 Teste 4: Funcionalidades de busca")
            results['search'] = test_shopee_search_functionality(shopee_api)
            
            # Teste 5: Busca geral (apenas se busca funcionou)
            if results['search']:
                logger.info("\n🎯 Teste 5: Busca geral de ofertas")
                results['general_search'] = test_shopee_general_search(shopee_api)
        
        # Teste 6: Formato dos dados
        logger.info("\n📊 Teste 6: Formato dos dados")
        results['data_format'] = test_shopee_data_format()
    
    # Teste 7: Função de conveniência
    logger.info("\n🔄 Teste 7: Função de conveniência")
    results['wrapper_function'] = test_shopee_function_wrapper()
    
    # Resumo dos resultados
    logger.info("\n" + "=" * 50)
    logger.info("📋 RESUMO DOS TESTES")
    logger.info("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\n📊 Resultado: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        logger.info("🎉 Todos os testes passaram! API da Shopee está funcionando perfeitamente!")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} teste(s) falharam. Verifique os logs acima.")
        return False

def main():
    """Função principal para executar os testes."""
    try:
        success = run_all_tests()
        
        if success:
            logger.info("\n🎯 Próximos passos:")
            logger.info("1. Configure suas credenciais da API da Shopee no arquivo .env")
            logger.info("2. Teste a integração no bot principal com: python main.py")
            logger.info("3. Monitore os logs para verificar o funcionamento")
        else:
            logger.error("\n❌ Alguns testes falharam. Verifique as configurações e tente novamente.")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Testes interrompidos pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"\n💥 Erro inesperado durante os testes: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
