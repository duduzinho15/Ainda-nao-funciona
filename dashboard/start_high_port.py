#!/usr/bin/env python3
"""
Script para usar porta alta (15000) - menos restritiva no Windows
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Função principal"""
    print("🚀 INICIANDO DASHBOARD NA PORTA 15000")
    print("=" * 50)
    print("💡 Porta alta pode ser menos restritiva no Windows")
    print()
    
    try:
        from app import app
        
        print("✅ App importado com sucesso")
        print("🌐 Iniciando servidor na porta 15000...")
        print("💡 Acesse: http://127.0.0.1:15000")
        print("⚠️  IMPORTANTE: Mantenha esta janela aberta!")
        print()
        
        # Configurações específicas para Windows
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        app.run(
            host='127.0.0.1',
            port=15000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\n💡 SOLUÇÕES:")
        print("   1. Execute como administrador")
        print("   2. Desative Windows Defender temporariamente")
        print("   3. Configure exceções no firewall")

if __name__ == "__main__":
    main()
