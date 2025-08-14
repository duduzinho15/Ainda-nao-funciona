import os
import hashlib
import requests
from datetime import datetime
from urllib.parse import urlencode, parse_qs
import json
import logging

# Configuração
APP_KEY = os.getenv('ALIEXPRESS_APP_KEY', '517956')
APP_SECRET = os.getenv('ALIEXPRESS_APP_SECRET', 'okv8nzEGIvWqV0XxONcN9loPNrYwWDsm')
TRACKING_ID = os.getenv('ALIEXPRESS_TRACKING_ID', 'telegram')
API_URL = "https://api-sg.aliexpress.com/sync"  # Endpoint de produção

def generate_sign(params, app_secret):
    """Gera a assinatura MD5 para a requisição."""
    # Ordena os parâmetros por chave
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    # Concatena os parâmetros
    string_to_sign = app_secret
    for key, value in sorted_params:
        if value is not None:
            string_to_sign += f"{key}{value}"
    string_to_sign += app_secret
    
    # Calcula o MD5
    return hashlib.md5(string_to_sign.encode('utf-8')).hexdigest().upper()

def test_affiliate_link_generation():
    """Testa a geração de links de afiliado (método básico)."""
    method = "aliexpress.affiliate.link.generate"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Configuração de logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ali_api_debug.log', encoding='utf-8')
        ]
    )
    logger = logging.getLogger('ali_api_test')
    
    # Parâmetros da requisição
    params = {
        'method': method,
        'app_key': APP_KEY,
        'sign_method': 'md5',
        'timestamp': timestamp,
        'v': '2.0',
        'format': 'json',
        'source_values': 'https://pt.aliexpress.com/item/1005009463783046.html',
        'tracking_id': TRACKING_ID,
        'country': 'BR',
        'target_currency': 'BRL',
        'target_language': 'PT',
        'promotion_link_type': '0'  # 0: Universal Link, 1: Deep Link, 2: Universal Link with coupon
    }
    
    # Gera a assinatura
    sign = generate_sign(params, APP_SECRET)
    params['sign'] = sign
    
    # Faz a requisição
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Accept': 'application/json'
    }
    
    logger.info("\n=== Testando geração de link de afiliado ===")
    logger.info(f"URL: {API_URL}")
    logger.info(f"Método: {method}")
    logger.info(f"Parâmetros: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    # Log da string de assinatura
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    string_to_sign = APP_SECRET + ''.join(f"{k}{v}" for k, v in sorted_params) + APP_SECRET
    logger.debug(f"String para assinatura: {string_to_sign}")
    
    try:
        # Faz a requisição
        logger.info("Enviando requisição...")
        response = requests.post(API_URL, data=params, headers=headers, timeout=30)
        
        # Log da resposta
        logger.info(f"Status da resposta: {response.status_code}")
        logger.info(f"Cabeçalhos da resposta: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logger.info("Resposta JSON:")
            logger.info(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # Salva a resposta completa em um arquivo
            with open('ali_api_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info("Resposta completa salva em 'ali_api_response.json'")
            
            # Exibe a resposta formatada no console
            print("\n=== RESPOSTA DA API ===")
            if 'error_response' in response_data:
                error = response_data['error_response']
                print(f"Erro: {error.get('msg', 'Erro desconhecido')}")
                print(f"Código: {error.get('code', 'N/A')}")
                print(f"Sub-código: {error.get('sub_code', 'N/A')}")
                print(f"Request ID: {error.get('request_id', 'N/A')}")
            else:
                print("Sucesso! Resposta recebida:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
        except json.JSONDecodeError:
            logger.error("Não foi possível decodificar a resposta como JSON")
            logger.error(f"Conteúdo da resposta: {response.text}")
            print(f"\nErro: A resposta não é um JSON válido. Conteúdo: {response.text[:500]}...")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {str(e)}", exc_info=True)
        print(f"\nErro na requisição: {str(e)}")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        print(f"\nErro inesperado: {str(e)}")

if __name__ == "__main__":
    test_affiliate_link_generation()
