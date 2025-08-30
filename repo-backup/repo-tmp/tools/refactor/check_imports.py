#!/usr/bin/env python3
"""
Script de Verificação de Imports
Verifica se há imports não resolvidos após refatoração
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

class ImportChecker:
    """Verificador de imports para detectar problemas"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.unresolved_imports = []
        self.import_errors = []
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("import_checker")
        
        # Módulos conhecidos (após refatoração)
        self.known_modules = {
            "src.core.scraper_registry",
            "src.core.normalize",
            "src.core.csv_exporter",
            "src.core.live_logs",
            "src.core.data_service",
            "src.core.rate_limiter",
            "src.core.logging_setup",
            "src.core.utils",
            "src.core.models",
            "src.core.settings",
            "src.core.storage",
            "src.core.database",
            "src.core.metrics",
            "src.core.affiliate_converter",
            "src.scrapers.base_scraper",
            "src.providers.base_api",
            "src.app.dashboard.dashboard",
            "src.app.bot.telegram_bot",
            "src.diagnostics.ui_reporter",
            "src.diagnostics.verify_snapshot",
            "src.diagnostics.smoke_sources",
            "src.posting.geek_auto_poster",
            "src.posting.notification_system",
            "src.recommender.price_comparator",
            "src.recommender.recommender",
            "src.recommender.rules",
        }
        
        # Módulos de terceiros conhecidos
        self.third_party_modules = {
            "flet", "aiohttp", "asyncio", "logging", "json", "re", "shutil",
            "argparse", "pathlib", "typing", "datetime", "sqlite3", "psutil",
            "requests", "beautifulsoup4", "selenium", "playwright", "pandas",
            "numpy", "pydantic", "plotly", "python_telegram_bot", "click",
            "rich", "tqdm", "pytest", "black", "flake8", "mypy", "ruff"
        }
    
    def scan_python_files(self) -> List[Path]:
        """Escaneia todos os arquivos Python no repositório"""
        python_files = []
        
        for root, dirs, files in os.walk(self.repo_root):
            # Pular diretórios que não devem ser escaneados
            dirs[:] = [d for d in dirs if d not in [
                '__pycache__', '.git', '.venv', 'venv', 'node_modules',
                'build', 'dist', '.pytest_cache', '.mypy_cache'
            ]]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def extract_imports_from_file(self, file_path: Path) -> List[Tuple[str, int, str]]:
        """Extrai imports de um arquivo Python"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST para extrair imports
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append((alias.name, node.lineno, "import"))
                    
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            if module:
                                full_name = f"{module}.{alias.name}"
                            else:
                                full_name = alias.name
                            imports.append((full_name, node.lineno, "from"))
                
            except SyntaxError as e:
                self.logger.warning(f"Erro de sintaxe em {file_path}: {e}")
                # Fallback: usar regex para imports básicos
                import_pattern = r'^(?:from\s+(\S+)\s+import|import\s+(\S+))'
                for line_num, line in enumerate(content.split('\n'), 1):
                    match = re.match(import_pattern, line.strip())
                    if match:
                        module = match.group(1) or match.group(2)
                        if module:
                            imports.append((module, line_num, "regex_fallback"))
        
        except Exception as e:
            self.logger.error(f"Erro ao ler {file_path}: {e}")
        
        return imports
    
    def check_import_resolution(self, import_name: str, file_path: Path) -> bool:
        """Verifica se um import pode ser resolvido"""
        # Verificar se é um módulo conhecido
        if import_name in self.known_modules:
            return True
        
        # Verificar se é um módulo de terceiros
        if import_name in self.third_party_modules:
            return True
        
        # Verificar se é um módulo de terceiros com submodules
        base_module = import_name.split('.')[0]
        if base_module in self.third_party_modules:
            return True
        
        # Verificar se é um módulo relativo
        if import_name.startswith('.'):
            return True
        
        # Verificar se é um módulo built-in
        try:
            __import__(import_name)
            return True
        except ImportError:
            pass
        
        # Verificar se o arquivo existe no sistema
        module_parts = import_name.split('.')
        possible_paths = []
        
        # Tentar diferentes localizações
        for i in range(len(module_parts), 0, -1):
            module_path = '.'.join(module_parts[:i])
            possible_paths.extend([
                self.repo_root / f"{module_path}.py",
                self.repo_root / module_path / "__init__.py",
                self.repo_root / "src" / f"{module_path}.py",
                self.repo_root / "src" / module_path / "__init__.py",
            ])
        
        for path in possible_paths:
            if path.exists():
                return True
        
        return False
    
    def check_file_imports(self, file_path: Path) -> List[Dict]:
        """Verifica imports de um arquivo específico"""
        issues = []
        imports = self.extract_imports_from_file(file_path)
        
        for import_name, line_num, import_type in imports:
            if not self.check_import_resolution(import_name, file_path):
                issue = {
                    'file': str(file_path),
                    'line': line_num,
                    'import': import_name,
                    'type': import_type,
                    'severity': 'error'
                }
                issues.append(issue)
                self.unresolved_imports.append(import_name)
        
        return issues
    
    def check_all_imports(self) -> Dict[str, List]:
        """Verifica imports em todos os arquivos Python"""
        all_issues = []
        python_files = self.scan_python_files()
        
        self.logger.info(f"🔍 Verificando imports em {len(python_files)} arquivos Python...")
        
        for file_path in python_files:
            issues = self.check_file_imports(file_path)
            all_issues.extend(issues)
            
            if issues:
                self.logger.warning(f"⚠️ {len(issues)} problemas encontrados em {file_path}")
        
        # Agrupar por severidade
        grouped_issues = {
            'errors': [i for i in all_issues if i['severity'] == 'error'],
            'warnings': [i for i in all_issues if i['severity'] == 'warning']
        }
        
        return grouped_issues
    
    def generate_report(self, issues: Dict[str, List]) -> str:
        """Gera relatório de verificação de imports"""
        report = []
        report.append("# 🔍 Relatório de Verificação de Imports")
        report.append("")
        report.append(f"**Data:** {Path().cwd()}")
        report.append("")
        
        # Resumo
        total_errors = len(issues.get('errors', []))
        total_warnings = len(issues.get('warnings', []))
        
        report.append("## 📊 Resumo")
        report.append(f"- Total de problemas: {total_errors + total_warnings}")
        report.append(f"- Erros: {total_errors}")
        report.append(f"- Avisos: {total_warnings}")
        report.append("")
        
        if total_errors == 0 and total_warnings == 0:
            report.append("✅ **Todos os imports estão resolvidos!**")
            report.append("")
        else:
            # Imports não resolvidos
            if issues.get('errors'):
                report.append("## ❌ Imports Não Resolvidos")
                report.append("")
                
                # Agrupar por arquivo
                by_file = {}
                for issue in issues['errors']:
                    file_path = issue['file']
                    if file_path not in by_file:
                        by_file[file_path] = []
                    by_file[file_path].append(issue)
                
                for file_path, file_issues in by_file.items():
                    report.append(f"### 📁 {file_path}")
                    report.append("")
                    
                    for issue in file_issues:
                        report.append(f"- **Linha {issue['line']}:** `{issue['import']}` ({issue['type']})")
                    
                    report.append("")
            
            # Avisos
            if issues.get('warnings'):
                report.append("## ⚠️ Avisos")
                report.append("")
                
                for issue in issues['warnings']:
                    report.append(f"- **{issue['file']}:{issue['line']}:** {issue['import']}")
                
                report.append("")
        
        # Módulos não resolvidos únicos
        if self.unresolved_imports:
            unique_unresolved = list(set(self.unresolved_imports))
            report.append("## 🔍 Módulos Não Resolvidos Únicos")
            report.append("")
            
            for module in sorted(unique_unresolved):
                report.append(f"- `{module}`")
            
            report.append("")
        
        # Recomendações
        report.append("## 🚀 Recomendações")
        if total_errors == 0:
            report.append("✅ Todos os imports estão funcionando corretamente!")
            report.append("✅ A refatoração foi bem-sucedida!")
        else:
            report.append("🔧 **Ações necessárias:**")
            report.append("1. Verificar se os módulos foram movidos corretamente")
            report.append("2. Atualizar imports que ainda referenciam caminhos antigos")
            report.append("3. Criar shims de compatibilidade se necessário")
            report.append("4. Verificar se os arquivos __init__.py foram criados")
            report.append("5. Executar testes para verificar funcionamento")
        
        return "\n".join(report)
    
    def run_check(self) -> bool:
        """Executa verificação completa de imports"""
        self.logger.info("🚀 Iniciando verificação de imports...")
        
        # Verificar imports
        issues = self.check_all_imports()
        
        # Gerar relatório
        report = self.generate_report(issues)
        
        # Salvar relatório
        report_file = self.repo_root / "tools/refactor/import_check_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Mostrar resumo
        print("\n" + "="*80)
        print(report)
        print("="*80)
        
        # Retornar sucesso (True se não há erros)
        return len(issues.get('errors', [])) == 0

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verificação de Imports - Garimpeiro Geek")
    parser.add_argument("--repo-root", type=str, default=".", 
                       help="Diretório raiz do repositório")
    parser.add_argument("--output", type=str, 
                       help="Arquivo de saída para o relatório")
    
    args = parser.parse_args()
    
    # Configurar diretório raiz
    repo_root = Path(args.repo_root).resolve()
    
    if not repo_root.exists():
        print(f"❌ Diretório não encontrado: {repo_root}")
        return 1
    
    # Executar verificação
    try:
        checker = ImportChecker(repo_root)
        success = checker.run_check()
        
        if success:
            print("✅ Verificação concluída com sucesso!")
            return 0
        else:
            print("❌ Problemas encontrados. Verifique o relatório.")
            return 1
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

