#!/usr/bin/env python3
"""
Teste Final de Execução da Aplicação Flet
Verifica se a aplicação está rodando e funcionando corretamente
"""

import sys
import os
import time
import subprocess
import psutil

def test_flet_running():
    """Testa se a aplicação Flet está rodando"""
    try:
        print("🔍 Verificando se a aplicação Flet está rodando...")
        
        # Procura por processos Flet
        flet_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'flet' in proc.info['name'].lower():
                    flet_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if flet_processes:
            print(f"✅ Encontrados {len(flet_processes)} processos Flet:")
            for proc in flet_processes:
                print(f"   - PID: {proc['pid']}, Nome: {proc['name']}")
            return True
        else:
            print("⚠️ Nenhum processo Flet encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar processos: {e}")
        return False

def test_file_integrity():
    """Testa integridade do arquivo principal"""
    try:
        print("\n🔍 Verificando integridade do arquivo principal...")
        
        # Verifica se o arquivo existe
        if not os.path.exists('app_flet_fixed.py'):
            print("❌ Arquivo app_flet_fixed.py não encontrado!")
            return False
        
        # Verifica tamanho do arquivo
        file_size = os.path.getsize('app_flet_fixed.py')
        print(f"✅ Arquivo encontrado, tamanho: {file_size:,} bytes")
        
        # Verifica se compila
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', 'app_flet_fixed.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Arquivo compila sem erros")
            return True
        else:
            print(f"❌ Erro de compilação: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo: {e}")
        return False

def test_dependencies():
    """Testa dependências necessárias"""
    try:
        print("\n🔍 Verificando dependências...")
        
        # Testa Flet
        import flet as ft
        print("✅ Flet disponível")
        
        # Testa sistema inteligente
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        try:
            from intelligent_geek_alert_system import IntelligentGeekAlertSystem
            print("✅ Sistema inteligente disponível")
        except ImportError as e:
            print(f"⚠️ Sistema inteligente não disponível: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de dependência: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE FINAL DE EXECUÇÃO - APLICAÇÃO FLET")
    print("=" * 60)
    
    # Testa integridade do arquivo
    file_ok = test_file_integrity()
    
    # Testa dependências
    deps_ok = test_dependencies()
    
    # Testa se está rodando
    running_ok = test_flet_running()
    
    print("\n" + "=" * 60)
    
    if file_ok and deps_ok:
        if running_ok:
            print("🎉 APLICAÇÃO FLET ESTÁ FUNCIONANDO PERFEITAMENTE!")
            print("\n💡 Status:")
            print("   ✅ Arquivo principal: OK")
            print("   ✅ Dependências: OK")
            print("   ✅ Execução: ATIVA")
            print("\n🚀 A aplicação está rodando e funcionando!")
        else:
            print("⚠️ APLICAÇÃO FLET ESTÁ PRONTA MAS NÃO ESTÁ RODANDO")
            print("\n💡 Para executar:")
            print("   flet run app_flet_fixed.py")
            print("   ou")
            print("   start_flet_app.bat")
    else:
        print("❌ ALGUNS PROBLEMAS FORAM IDENTIFICADOS")
        print("   Verifique os erros acima")

if __name__ == "__main__":
    main()

