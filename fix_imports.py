#!/usr/bin/env python3
"""
Script para corrigir problemas de importação automaticamente.
Execute este script para resolver problemas de importação no VS Code/Cursor.
"""

import sys
import os
import subprocess
import json


def main():
    print("🔧 Corrigindo problemas de importação...")

    # 1. Verifica se o ambiente virtual existe
    venv_path = os.path.join(os.path.dirname(__file__), "venv")
    if not os.path.exists(venv_path):
        print("❌ Ambiente virtual não encontrado!")
        print("💡 Execute: python -m venv venv")
        return False

    # 2. Verifica se as dependências estão instaladas
    try:
        import telegram

        print("✅ Módulo telegram já está funcionando!")
        return True
    except ImportError:
        print("⚠️ Módulo telegram não pode ser importado. Instalando dependências...")

    # 3. Instala as dependências
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✅ Dependências instaladas com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

    # 4. Testa as importações novamente
    try:
        import telegram
        from telegram import Update, BotCommand
        from telegram.constants import ParseMode
        from telegram.ext import Application, CommandHandler, ContextTypes

        print("✅ Todas as importações estão funcionando!")
    except ImportError as e:
        print(f"❌ Erro de importação persistente: {e}")
        return False

    # 5. Cria/atualiza arquivos de configuração
    print("📝 Criando arquivos de configuração...")

    # Configuração do VS Code
    vscode_dir = ".vscode"
    os.makedirs(vscode_dir, exist_ok=True)

    vscode_settings = {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.terminal.activateEnvironment": True,
        "python.analysis.extraPaths": [
            "./venv/Lib/site-packages",
            "./venv/Lib/site-packages/telegram",
            "./venv/Lib/site-packages/telegram/ext",
        ],
        "python.analysis.autoImportCompletions": True,
        "python.analysis.typeCheckingMode": "basic",
        "python.analysis.include": ["**/*.py"],
        "python.analysis.exclude": ["**/venv/**", "**/__pycache__/**", "**/*.pyc"],
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": False,
        "python.linting.flake8Enabled": False,
        "python.linting.mypyEnabled": False,
        "python.analysis.diagnosticMode": "workspace",
        "python.analysis.stubPath": "./venv/Lib/site-packages",
        "python.analysis.autoSearchPaths": True,
        "python.analysis.useLibraryCodeForTypes": True,
        "python.analysis.completeFunctionParens": True,
    }

    with open(os.path.join(vscode_dir, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(vscode_settings, f, indent=4)

    # Configuração do Pyright
    pyright_config = {
        "include": ["."],
        "exclude": [
            "**/venv",
            "**/__pycache__",
            "**/*.pyc",
            "**/node_modules",
            "**/.git",
        ],
        "ignore": ["**/venv/**"],
        "reportMissingImports": "warning",
        "reportMissingTypeStubs": False,
        "pythonVersion": "3.13",
        "pythonPlatform": "Windows",
        "executionEnvironments": [
            {
                "root": ".",
                "pythonVersion": "3.13",
                "pythonPlatform": "Windows",
                "extraPaths": [
                    "./venv/Lib/site-packages",
                    "./venv/Lib/site-packages/telegram",
                    "./venv/Lib/site-packages/telegram/ext",
                ],
            }
        ],
        "typeCheckingMode": "basic",
        "useLibraryCodeForTypes": True,
        "autoImportCompletions": True,
    }

    with open("pyrightconfig.json", "w", encoding="utf-8") as f:
        json.dump(pyright_config, f, indent=4)

    print("✅ Arquivos de configuração criados/atualizados!")

    # 6. Instruções finais
    print("\n🎉 Problema de importação resolvido!")
    print("\n📋 Próximos passos:")
    print("1. Feche e reabra o VS Code/Cursor")
    print("2. Pressione Ctrl+Shift+P e digite 'Python: Select Interpreter'")
    print("3. Selecione: ./venv/Scripts/python.exe")
    print(
        "4. Reinicie o servidor de linguagem Python (Ctrl+Shift+P > 'Python: Restart Language Server')"
    )
    print("\n💡 Se o problema persistir, execute: python fix_imports.py")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
