#!/usr/bin/env python3
"""
Script de teste mínimo para a API de afiliados do AliExpress.

Este script testa a autenticação básica e a obtenção de informações de um produto.
"""
import os
import sys
import json
import logging
import hashlib
import urllib.parse
from datetime import datetime
import requests
from dotenv import load_dotenv

# Configuração básica de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ali_test')

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da API
API_URL = "http://gw.api.taobao.com/router/rest"
API_VERSION = "2.0"
SIGN_METHOD = "md5"
RESPONSE_FORMAT = "json"

def generate_sign(params, app_secret):
    """Gera a assinatura para a requisição à API."""
    # Ordena os parâmetros por chave
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    # Concatena os parâmetros
    string_to_sign = app_secret
    for key, value in sorted_params:
        if value is not None:
            string_to_sign += f"{key}{value}"
    string_to_sign += app_secret
    
    # Calcula o MD5
    signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest().upper()
    return signature

def test_api_connection():
    """Testa a conexão com a API do AliExpress."""
    # Obtém as credenciais do ambiente
    app_key = os.getenv('ALIEXPRESS_APP_KEY')
    app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
    tracking_id = os.getenv('ALIEXPRESS_TRACKING_ID')
    
    if not all([app_key, app_secret, tracking_id]):
        logger.error("Credenciais da API não encontradas no arquivo .env")
        return False
    
    # ID de um produto de teste (um produto popular no AliExpress)
    product_id = "1005009463783046"  # Exemplo de ID de produto
    
    # Parâmetros da requisição
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    params = {
        'app_key': app_key,
        'method': 'aliexpress.affiliate.productdetail.get',
        'timestamp': timestamp,
        'format': RESPONSE_FORMAT,
        'v': API_VERSION,
        'sign_method': SIGN_METHOD,
        'partner_id': 'garimpeiro_geek',
        'product_ids': product_id,
        'target_currency': 'BRL',
        'target_language': 'PT',
        'tracking_id': tracking_id,
        'country': 'BR'
    }
    
    # Gera a assinatura
    sign = generate_sign(params, app_secret)
    params['sign'] = sign
    
    # Faz a requisição
    try:
        logger.info("Enviando requisição para a API do AliExpress...")
        logger.debug(f"URL: {API_URL}")
        logger.debug(f"Parâmetros: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        
        response = requests.post(
            API_URL,
            data=params,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Resposta recebida. Status: {response.status_code}")
        
        try:
            result = response.json()
            logger.info("Resposta JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Salva a resposta em um arquivo para análise
            with open('ali_api_response.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar a resposta JSON: {e}")
            logger.error(f"Conteúdo da resposta: {response.text[:1000]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        return False

def main():
    """Função principal."""
    logger.info("Iniciando teste de conexão com a API do AliExpress...")
    
    success = test_api_connection()
    
    if success:
        logger.info("Teste concluído com sucesso! Verifique o arquivo ali_api_response.json para os detalhes.")
    else:
        logger.error("Ocorreu um erro durante o teste. Verifique os logs para mais detalhes.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
