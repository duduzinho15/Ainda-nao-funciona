#!/usr/bin/env python3
"""
Script de execução para o Dashboard Flet
Garante que os imports funcionem corretamente independente de como é executado
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Configura o Python path para encontrar os módulos src"""
    # Obter o diretório raiz do projeto
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    
    # Adicionar ao Python path se não estiver presente
    project_root_str = str(project_root.resolve())
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    # Também adicionar o diretório do dashboard para imports relativos
    dashboard_dir = str(current_file.parent.resolve())
    if dashboard_dir not in sys.path:
        sys.path.insert(0, dashboard_dir)
    
    print(f"✅ Python path configurado:")
    print(f"   Projeto: {project_root_str}")
    print(f"   Dashboard: {dashboard_dir}")

def main():
    """Função principal que configura o ambiente e executa o dashboard"""
    try:
        # Configurar Python path
        setup_python_path()
        
        # Importar e executar o dashboard
        import flet as ft
        from main import GarimpeiroDashboard
        
        print("🚀 Iniciando Dashboard Flet...")
        dashboard = GarimpeiroDashboard()
        
        # Executar o dashboard
        ft.app(
            target=dashboard.main,
            name="Garimpeiro Geek - Dashboard",
            port=8550,
            view=ft.AppView.WEB_BROWSER
        )
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("\n💡 Soluções possíveis:")
        print("   1. Execute a partir do diretório raiz do projeto")
        print("   2. Verifique se todas as dependências estão instaladas")
        print("   3. Execute: python -m apps.flet_dashboard.run_dashboard")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

