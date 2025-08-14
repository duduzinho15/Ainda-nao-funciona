#!/usr/bin/env python3
"""
Script simples para iniciar o Dashboard Garimpeiro Geek
Executa diretamente sem problemas de caminho
"""

import os
import sys
from pathlib import Path

def main():
    """Função principal"""
    print("🚀 INICIANDO DASHBOARD GARIMPEIRO GEEK")
    print("=" * 50)
    
    try:
        # Adiciona o diretório raiz ao path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        print(f"📁 Diretório do projeto: {project_root}")
        
        # Importa o app
        from app import app
        
        print("✅ App importado com sucesso")
        print("🌐 Iniciando servidor na porta 8080...")
        print("💡 Acesse: http://127.0.0.1:8080")
        print("⚠️  IMPORTANTE: Mantenha esta janela aberta!")
        print()
        
        # Configurações específicas para Windows
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Inicia o servidor
        app.run(
            host='127.0.0.1',
            port=8080,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("\n💡 SOLUÇÕES:")
        print("   1. Execute como administrador")
        print("   2. Verifique se o ambiente virtual está ativado")
        print("   3. Execute: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        print("\n💡 SOLUÇÕES:")
        print("   1. Execute como administrador")
        print("   2. Desative Windows Defender temporariamente")
        print("   3. Configure exceções no firewall")

if __name__ == "__main__":
    main()
