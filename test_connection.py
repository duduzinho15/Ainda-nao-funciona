#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simples para testar a conexão com o site do Magazine Luiza.
"""

import requests
import sys

def test_connection():
    """Testa a conexão com o site do Magazine Luiza."""
    print("Testando conexão com o Magazine Luiza...")
    
    url = "https://www.magazineluiza.com.br/"
    
    try:
        # Configuração do User-Agent para simular um navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fazendo requisição para: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
        
        print(f"\n✅ Conexão bem-sucedida!")
        print(f"Status Code: {response.status_code}")
        print(f"Tamanho da resposta: {len(response.text)} bytes")
        print(f"Tipo de conteúdo: {response.headers.get('content-type')}")
        
        # Verifica se a resposta parece ser do Magazine Luiza
        if 'magazineluiza' in response.text.lower():
            print("✅ Conteúdo parece ser do Magazine Luiza")
        else:
            print("⚠️  O conteúdo não parece ser do Magazine Luiza")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro na conexão: {e}")
        if isinstance(e, requests.exceptions.SSLError):
            print("Erro de certificado SSL. Pode ser necessário atualizar seus certificados.")
        elif isinstance(e, requests.exceptions.ConnectTimeout):
            print("Tempo limite de conexão excedido. Verifique sua conexão com a internet.")
        elif isinstance(e, requests.exceptions.ConnectionError):
            print("Erro de conexão. Verifique sua conexão com a internet.")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE CONEXÃO COM O MAGAZINE LUÍZA")
    print("=" * 60)
    
    success = test_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("❌ TESTE FALHOU. Verifique a mensagem de erro acima.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
