#!/usr/bin/env python3
"""
Runner Principal de Testes - Sistema de Recomendações de Ofertas
Executa todos os testes automatizados do projeto
"""

import unittest
import sys
import os
import time
from pathlib import Path

def discover_and_run_tests():
    """Descobre e executa todos os testes do projeto"""
    print("🧪 Sistema de Testes Automatizados - Garimpeiro Geek")
    print("=" * 60)
    
    # Diretório raiz dos testes
    test_dir = Path(__file__).parent
    
    # Descobrir todos os arquivos de teste
    test_files = list(test_dir.glob("test_*.py"))
    
    print(f"📁 Diretório de testes: {test_dir}")
    print(f"🔍 Arquivos de teste encontrados: {len(test_files)}")
    
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    print("\n" + "=" * 60)
    
    # Criar loader de testes
    loader = unittest.TestLoader()
    
    # Descobrir testes automaticamente
    suite = loader.discover(
        start_dir=str(test_dir),
        pattern="test_*.py",
        top_level_dir=str(test_dir.parent.parent)
    )
    
    # Executar testes
    print("🚀 Executando testes...")
    start_time = time.time()
    
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Resumo detalhado
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL DOS TESTES")
    print("=" * 60)
    
    print(f"⏱️  Tempo de execução: {execution_time:.2f} segundos")
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️  Erros: {len(result.errors)}")
    print(f"⏭️  Testes ignorados: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # Detalhes das falhas
    if result.failures:
        print(f"\n❌ FALHAS ENCONTRADAS ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n{i}. {test}")
            print(f"   Erro: {traceback.split('AssertionError:')[-1].strip()}")
    
    # Detalhes dos erros
    if result.errors:
        print(f"\n⚠️  ERROS ENCONTRADOS ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n{i}. {test}")
            print(f"   Erro: {traceback.split('Exception:')[-1].strip()}")
    
    # Resultado final
    print("\n" + "=" * 60)
    
    if result.wasSuccessful():
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("✅ Sistema está funcionando perfeitamente!")
        return True
    else:
        print("💥 ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique os erros acima e corrija os problemas.")
        return False

def run_specific_test(test_name):
    """Executa um teste específico"""
    print(f"🎯 Executando teste específico: {test_name}")
    
    test_dir = Path(__file__).parent
    test_file = test_dir / f"test_{test_name}.py"
    
    if not test_file.exists():
        print(f"❌ Arquivo de teste não encontrado: {test_file}")
        return False
    
    # Executar teste específico
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f"test_{test_name}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        # Executar teste específico
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Executar todos os testes
        success = discover_and_run_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
