#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste mínimo para a integração com a API da Amazon PA-API.

Este script testa apenas a funcionalidade básica de busca de produtos,
com logging detalhado para facilitar a depuração.
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('paapi_test.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger('paapi_test')

# Credenciais da API (substitua pelos seus valores reais)
CREDENTIALS = {
    'access_key': os.getenv('AMAZON_ACCESS_KEY', 'YOUR_ACCESS_KEY'),
    'secret_key': os.getenv('AMAZON_SECRET_KEY', 'YOUR_SECRET_KEY'),
    'associate_tag': os.getenv('AMAZON_ASSOCIATE_TAG', 'YOUR_ASSOCIATE_TAG'),
    'host': 'webservices.amazon.com.br',
    'region': 'us-west-2',
    'uri': '/paapi5/searchitems'
}

def test_paapi_request():
    """Testa uma requisição básica para a API da Amazon PA-API."""
    logger.info("🚀 Iniciando teste de requisição para a API da Amazon PA-API...")
    
    # Verifica se as credenciais estão configuradas
    if any(v.startswith('YOUR_') for k, v in CREDENTIALS.items() if k != 'host' and k != 'region' and k != 'uri'):
        logger.error("❌ Credenciais não configuradas corretamente. Verifique o arquivo de configuração.")
        return False
    
    # Cabeçalhos da requisição
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': CREDENTIALS['host'],
        'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems',
        'Content-Encoding': 'amz-1.0'
    }
    
    # Corpo da requisição
    payload = {
        'Keywords': 'smartphone',
        'ItemCount': 5,
        'PartnerTag': CREDENTIALS['associate_tag'],
        'PartnerType': 'Associates',
        'Resources': [
            'Images.Primary.Large',
            'ItemInfo.Title',
            'Offers.Listings.Price',
            'ItemInfo.Features',
            'Offers.Listings.SavingBasis',
            'Offers.Listings.Condition',
            'Offers.Listings.IsBuyBoxWinner'
        ],
        'SearchIndex': 'Electronics',
        'ItemCondition': 'New',
        'Merchant': 'Amazon',
        'LanguagesOfPreference': ['pt_BR'],
        'CurrencyOfPreference': 'BRL',
        'Marketplace': 'www.amazon.com.br'
    }
    
    # URL da API
    url = f"https://{CREDENTIALS['host']}{CREDENTIALS['uri']}"
    
    logger.info(f"🔍 Enviando requisição para: {url}")
    logger.debug(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        # Faz a requisição diretamente (sem assinatura para teste)
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"✅ Resposta recebida - Status: {response.status_code}")
        logger.debug(f"📋 Cabeçalhos da resposta: {dict(response.headers)}")
        
        # Tenta decodificar a resposta JSON
        try:
            response_json = response.json()
            logger.info("📄 Resposta JSON recebida com sucesso!")
            
            # Salva a resposta em um arquivo para análise
            with open('paapi_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_json, f, indent=2, ensure_ascii=False)
            
            # Verifica se há erros na resposta
            if 'Errors' in response_json:
                for error in response_json.get('Errors', []):
                    logger.error(f"❌ Erro da API: {error.get('Code')} - {error.get('Message')}")
                return False
            
            # Verifica se há resultados
            if 'SearchResult' in response_json and 'Items' in response_json['SearchResult']:
                items = response_json['SearchResult']['Items']
                logger.info(f"🎉 Sucesso! {len(items)} itens retornados.")
                
                # Exibe informações básicas dos itens
                for i, item in enumerate(items, 1):
                    title = item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'Sem título')
                    asin = item.get('ASIN', 'N/A')
                    logger.info(f"\n📦 Item #{i}")
                    logger.info(f"   Título: {title}")
                    logger.info(f"   ASIN: {asin}")
                    
                    # Tenta obter o preço
                    price_info = item.get('Offers', {}).get('Listings', [{}])[0].get('Price', {})
                    if price_info:
                        amount = price_info.get('Amount', 0)
                        currency = price_info.get('Currency', 'BRL')
                        decimals = currency.get('Decimals', 2)
                        price = amount / (10 ** decimals)
                        logger.info(f"   Preço: R$ {price:.2f}")
                
                return True
            else:
                logger.warning("⚠️  Nenhum item encontrado na resposta.")
                return False
            
        except json.JSONDecodeError as je:
            logger.error(f"❌ Falha ao decodificar resposta JSON: {je}")
            logger.error(f"📝 Conteúdo da resposta: {response.text[:2000]}...")
            return False
    
    except requests.exceptions.RequestException as re:
        logger.error(f"❌ Erro na requisição HTTP: {str(re)}")
        if hasattr(re, 'response') and re.response is not None:
            logger.error(f"📝 Resposta do servidor: {re.response.text[:2000] if re.response.text else 'Sem conteúdo'}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE MÍNIMO - AMAZON PA-API")
    print("=" * 60)
    print("")
    
    # Executa o teste
    sucesso = test_paapi_request()
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!" if sucesso else "❌ TESTE FALHOU!")
    print("=" * 60)
    print("\nVerifique o arquivo 'paapi_test.log' para logs detalhados.")
    if sucesso:
        print("A resposta completa foi salva em 'paapi_response.json'.")
