#!/usr/bin/env python3
"""
Script para testar a API da Awin e verificar Publisher IDs
"""
import asyncio
import aiohttp
import config
import json

async def test_awin_api():
    """Testa a API da Awin com diferentes endpoints e Publisher IDs"""
    
    print("🧪 TESTANDO API DA AWIN")
    print("=" * 50)
    
    # Configurações
    api_base = "https://api.awin.com"
    api_version = "v1"
    token = config.AWIN_API_TOKEN
    
    # Publisher IDs para testar
    publisher_ids = [
        "2510157",  # ID principal
        "2370719",  # ID Samsung
        "1234567",  # ID de teste (deve falhar)
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Teste 1: Verificar se a API está acessível
        print("\n🔍 Teste 1: Verificando acessibilidade da API")
        try:
            async with session.get(f"{api_base}/", headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    print("   ✅ API acessível")
                else:
                    print("   ⚠️ API retornou status inesperado")
        except Exception as e:
            print(f"   ❌ Erro ao acessar API: {e}")
        
        # Teste 2: Verificar diferentes versões da API
        print("\n🔍 Teste 2: Testando diferentes versões da API")
        api_versions = ["v1", "v2", "v3"]
        
        for version in api_versions:
            try:
                url = f"{api_base}/{version}/publishers/2510157/programmes"
                async with session.get(url, headers=headers) as response:
                    print(f"   Versão {version}: HTTP {response.status}")
                    if response.status == 200:
                        print(f"   ✅ Versão {version} funciona!")
                        break
                    elif response.status == 404:
                        print(f"   ❌ Versão {version} não encontrada")
                    else:
                        print(f"   ⚠️ Versão {version} retornou {response.status}")
            except Exception as e:
                print(f"   ❌ Erro ao testar versão {version}: {e}")
        
        # Teste 3: Testar diferentes endpoints
        print("\n🔍 Teste 3: Testando diferentes endpoints")
        endpoints = [
            "programmes",
            "programmes?relationship=joined",
            "programmes?relationship=approved",
            "advertisers",
            "publishers"
        ]
        
        working_version = "v1"  # Usa a versão que funcionou no teste anterior
        
        for endpoint in endpoints:
            try:
                url = f"{api_base}/{working_version}/publishers/2510157/{endpoint}"
                async with session.get(url, headers=headers) as response:
                    print(f"   Endpoint {endpoint}: HTTP {response.status}")
                    if response.status == 200:
                        print(f"   ✅ Endpoint {endpoint} funciona!")
                        # Tenta ler a resposta para ver o formato
                        try:
                            data = await response.json()
                            print(f"   📊 Resposta: {len(data.get('data', []))} itens")
                        except:
                            print(f"   📊 Resposta não é JSON válido")
                    elif response.status == 404:
                        print(f"   ❌ Endpoint {endpoint} não encontrado")
                    else:
                        print(f"   ⚠️ Endpoint {endpoint} retornou {response.status}")
            except Exception as e:
                print(f"   ❌ Erro ao testar endpoint {endpoint}: {e}")
        
        # Teste 4: Testar diferentes Publisher IDs
        print("\n🔍 Teste 4: Testando diferentes Publisher IDs")
        
        for pub_id in publisher_ids:
            try:
                url = f"{api_base}/{working_version}/publishers/{pub_id}/programmes"
                async with session.get(url, headers=headers) as response:
                    print(f"   Publisher ID {pub_id}: HTTP {response.status}")
                    if response.status == 200:
                        print(f"   ✅ Publisher ID {pub_id} válido!")
                        try:
                            data = await response.json()
                            print(f"   📊 Programas encontrados: {len(data.get('data', []))}")
                        except:
                            print(f"   📊 Resposta não é JSON válido")
                    elif response.status == 404:
                        print(f"   ❌ Publisher ID {pub_id} não encontrado")
                    elif response.status == 401:
                        print(f"   🔒 Publisher ID {pub_id} não autorizado")
                    else:
                        print(f"   ⚠️ Publisher ID {pub_id} retornou {response.status}")
            except Exception as e:
                print(f"   ❌ Erro ao testar Publisher ID {pub_id}: {e}")
        
        # Teste 5: Verificar se o token está válido
        print("\n🔍 Teste 5: Verificando validade do token")
        try:
            # Tenta acessar um endpoint que deve funcionar se o token for válido
            url = f"{api_base}/{working_version}/publishers"
            async with session.get(url, headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    print("   ✅ Token válido")
                elif response.status == 401:
                    print("   ❌ Token inválido ou expirado")
                else:
                    print(f"   ⚠️ Status inesperado: {response.status}")
        except Exception as e:
            print(f"   ❌ Erro ao verificar token: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 TESTES CONCLUÍDOS")

if __name__ == "__main__":
    asyncio.run(test_awin_api())
