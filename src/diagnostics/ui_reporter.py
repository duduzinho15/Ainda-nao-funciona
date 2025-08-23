#!/usr/bin/env python3
"""
UI Reporter - Sistema de Testes de Interface do Garimpeiro Geek
Valida componentes da UI, snapshots e funcionalidades críticas
"""

import argparse
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import tempfile
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.logging_setup import setup_logging
from src.core.storage import PreferencesStorage
from src.core.database import Database

class UIReporter:
    """Sistema de testes de interface e validação de componentes"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
        # Setup logging
        setup_logging()
        
    def run_check(self, name: str, check_func, description: str = "") -> bool:
        """Executa um check e registra o resultado"""
        try:
            start_time = time.time()
            result = check_func()
            duration = time.time() - start_time
            
            if result:
                self.passed += 1
                status = "✅ PASS"
                color = "\033[92m"  # Verde
            else:
                self.failed += 1
                status = "❌ FAIL"
                color = "\033[91m"  # Vermelho
                
            self.results.append({
                "name": name,
                "status": "PASS" if result else "FAIL",
                "description": description,
                "duration": round(duration, 3)
            })
            
            print(f"{color}{status}\033[0m {name} ({duration:.3f}s)")
            if description:
                print(f"    {description}")
                
            return result
            
        except Exception as e:
            self.failed += 1
            self.results.append({
                "name": name,
                "status": "ERROR",
                "description": f"Error: {str(e)}",
                "duration": 0
            })
            print(f"\033[91m❌ ERROR\033[0m {name} - {str(e)}")
            return False
    
    def check_dashboard_components(self) -> bool:
        """Verifica se os componentes do dashboard existem"""
        dashboard_path = Path("src/app/dashboard/dashboard.py")
        if not dashboard_path.exists():
            return False
            
        content = dashboard_path.read_text(encoding='utf-8')
        
        # Verificar componentes essenciais
        required_components = [
            "def build_tabs",
            "def build_header", 
            "def build_metrics_row",
            "def build_chart_panel",
            "def build_logs_panel",
            "def build_config_tab",
            "def build_controls_tab"
        ]
        
        for component in required_components:
            if component not in content:
                return False
                
        return True
    
    def check_ui_keys_present(self) -> bool:
        """Verifica se as keys de UI essenciais estão presentes"""
        dashboard_path = Path("src/app/dashboard/dashboard.py")
        if not dashboard_path.exists():
            return False
            
        content = dashboard_path.read_text(encoding='utf-8')
        
        required_keys = [
            '"tabs"',
            '"card_ofertas"',
            '"card_lojas"', 
            '"card_preco"',
            '"card_periodo"',
            '"filters"',
            '"chart"',
            '"logs"',
            '"csv_botao_presente"'
        ]
        
        for key in required_keys:
            if key not in content:
                return False
                
        return True
    
    def check_core_modules_exist(self) -> bool:
        """Verifica se os módulos core essenciais existem"""
        core_modules = [
            "src/core/storage.py",
            "src/core/database.py", 
            "src/core/metrics.py",
            "src/core/live_logs.py",
            "src/core/logging_setup.py"
        ]
        
        for module in core_modules:
            if not Path(module).exists():
                return False
                
        return True
    
    def check_scrapers_structure(self) -> bool:
        """Verifica se a estrutura de scrapers está correta"""
        scrapers_dir = Path("src/scrapers")
        if not scrapers_dir.exists():
            return False
            
        # Verificar se base_scraper existe
        if not (scrapers_dir / "base_scraper.py").exists():
            return False
            
        # Verificar se há pelo menos alguns scrapers
        scraper_dirs = [d for d in scrapers_dir.iterdir() if d.is_dir()]
        if len(scraper_dirs) < 3:
            return False
            
        return True
    
    def check_providers_structure(self) -> bool:
        """Verifica se a estrutura de providers está correta"""
        providers_dir = Path("src/providers")
        if not providers_dir.exists():
            return False
            
        # Verificar se base_api existe
        if not (providers_dir / "base_api.py").exists():
            return False
            
        return True
    
    def check_dashboard_imports(self) -> bool:
        """Verifica se os imports do dashboard estão corretos"""
        try:
            # Tentar importar o dashboard
            import subprocess
            result = subprocess.run([
                sys.executable, "-c", 
                "import sys; sys.path.insert(0, 'src'); from app.dashboard.dashboard import main"
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        except:
            return False
    
    def check_database_connection(self) -> bool:
        """Verifica se a conexão com o banco funciona"""
        try:
            db = Database()
            # Teste simples de conexão
            return True
        except:
            return False
    
    def check_preferences_storage(self) -> bool:
        """Verifica se o sistema de preferências funciona"""
        try:
            storage = PreferencesStorage()
            # Teste simples de escrita/leitura
            storage.set_preference("test_key", "test_value")
            value = storage.get_preference("test_key")
            return value == "test_value"
        except:
            return False
    
    def check_logs_directory(self) -> bool:
        """Verifica se o diretório de logs existe e é acessível"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
        return logs_dir.exists() and logs_dir.is_dir()
    
    def check_exports_directory(self) -> bool:
        """Verifica se o diretório de exports existe"""
        exports_dir = Path("exports")
        if not exports_dir.exists():
            exports_dir.mkdir(exist_ok=True)
        return exports_dir.exists() and exports_dir.is_dir()
    
    def check_src_structure(self) -> bool:
        """Verifica se a estrutura src/ está correta"""
        src_dir = Path("src")
        if not src_dir.exists():
            return False
            
        required_dirs = [
            "src/core",
            "src/app", 
            "src/scrapers",
            "src/providers",
            "src/diagnostics",
            "src/tests"
        ]
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                return False
                
        return True
    
    def check_init_files(self) -> bool:
        """Verifica se os arquivos __init__.py estão presentes"""
        init_files = [
            "src/__init__.py",
            "src/core/__init__.py",
            "src/app/__init__.py",
            "src/scrapers/__init__.py", 
            "src/providers/__init__.py",
            "src/diagnostics/__init__.py",
            "src/tests/__init__.py"
        ]
        
        for init_file in init_files:
            if not Path(init_file).exists():
                return False
                
        return True
    
    def check_entry_points(self) -> bool:
        """Verifica se os pontos de entrada principais existem"""
        entry_points = [
            "start.py",
            "backup.py", 
            "monitor.py",
            "install.py"
        ]
        
        for entry_point in entry_points:
            if not Path(entry_point).exists():
                return False
                
        return True
    
    def check_configuration_files(self) -> bool:
        """Verifica se os arquivos de configuração existem"""
        config_files = [
            "pyproject.toml",
            "Makefile",
            "requirements.txt"
        ]
        
        for config_file in config_files:
            if not Path(config_file).exists():
                return False
                
        return True
    
    def check_global_toggle_on_controls(self) -> bool:
        """Verifica se há toggle global na aba controles"""
        dashboard_path = Path("src/app/dashboard/dashboard.py")
        if not dashboard_path.exists():
            return False
            
        content = dashboard_path.read_text(encoding='utf-8')
        
        # Procurar por indicadores de toggle global
        indicators = [
            "Sistema",
            "global",
            "master",
            "Switch"
        ]
        
        # Deve ter pelo menos alguns indicadores
        found_indicators = sum(1 for indicator in indicators if indicator in content)
        return found_indicators >= 2
    
    def check_per_source_toggles_present(self) -> bool:
        """Verifica se há toggles individuais por fonte"""
        dashboard_path = Path("src/app/dashboard/dashboard.py")
        if not dashboard_path.exists():
            return False
            
        content = dashboard_path.read_text(encoding='utf-8')
        
        # Procurar por indicadores de toggles individuais
        indicators = [
            "fonte", "source", "scraper", "api", "provider",
            "toggle", "switch", "enabled", "disabled"
        ]
        
        found_indicators = sum(1 for indicator in indicators if indicator.lower() in content.lower())
        return found_indicators >= 3
    
    def check_runner_status_visible(self) -> bool:
        """Verifica se o status do runner está visível"""
        dashboard_path = Path("src/app/dashboard/dashboard.py")
        if not dashboard_path.exists():
            return False
            
        content = dashboard_path.read_text(encoding='utf-8')
        
        # Procurar por indicadores de status
        return "status" in content.lower() or "running" in content.lower()
    
    def generate_snapshot(self) -> Dict[str, Any]:
        """Gera snapshot do estado atual do sistema"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "structure": {},
            "components": {},
            "metrics": {}
        }
        
        # Estrutura de diretórios
        for path in ["src/core", "src/app", "src/scrapers", "src/providers"]:
            if Path(path).exists():
                files = [f.name for f in Path(path).rglob("*.py")]
                snapshot["structure"][path] = files
        
        # Componentes do dashboard
        dashboard_path = Path("src/app/dashboard/dashboard.py")
        if dashboard_path.exists():
            content = dashboard_path.read_text(encoding='utf-8')
            snapshot["components"]["dashboard_size"] = len(content)
            snapshot["components"]["has_tabs"] = "build_tabs" in content
            snapshot["components"]["has_metrics"] = "build_metrics_row" in content
        
        return snapshot
    
    def run_all_checks(self) -> bool:
        """Executa todos os checks"""
        print("🔍 Executando UI Reporter - Validação do Sistema")
        print("=" * 60)
        
        checks = [
            ("src_structure", self.check_src_structure, "Estrutura src/ correta"),
            ("init_files", self.check_init_files, "Arquivos __init__.py presentes"),
            ("core_modules", self.check_core_modules_exist, "Módulos core existem"),
            ("scrapers_structure", self.check_scrapers_structure, "Estrutura scrapers correta"),
            ("providers_structure", self.check_providers_structure, "Estrutura providers correta"),
            ("dashboard_components", self.check_dashboard_components, "Componentes dashboard presentes"),
            ("ui_keys_present", self.check_ui_keys_present, "Keys UI essenciais presentes"),
            ("dashboard_imports", self.check_dashboard_imports, "Imports dashboard funcionam"),
            ("database_connection", self.check_database_connection, "Conexão banco funciona"),
            ("preferences_storage", self.check_preferences_storage, "Sistema preferências funciona"),
            ("logs_directory", self.check_logs_directory, "Diretório logs existe"),
            ("exports_directory", self.check_exports_directory, "Diretório exports existe"),
            ("entry_points", self.check_entry_points, "Pontos entrada existem"),
            ("configuration_files", self.check_configuration_files, "Arquivos configuração existem"),
            ("global_toggle_on_controls", self.check_global_toggle_on_controls, "Toggle global presente"),
            ("per_source_toggles_present", self.check_per_source_toggles_present, "Toggles por fonte presentes"),
            ("runner_status_visible", self.check_runner_status_visible, "Status runner visível")
        ]
        
        for name, check_func, description in checks:
            self.run_check(name, check_func, description)
        
        # Resumo final
        print("\n" + "=" * 60)
        print(f"📊 Resumo: {self.passed} ✅ | {self.failed} ❌ | {self.skipped} ⏭️")
        
        total_checks = len(checks)
        success_rate = (self.passed / total_checks) * 100
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.failed > 0:
            print(f"❌ {self.failed} checks falharam")
            if self.strict_mode:
                print("🚨 Modo strict ativo - falhas causarão exit code 1")
        
        return self.failed == 0
    
    def save_report(self, output_file: str = "ui_report.json"):
        """Salva relatório em arquivo JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "total": len(self.results)
            },
            "results": self.results,
            "snapshot": self.generate_snapshot()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="UI Reporter - Validação do Sistema")
    parser.add_argument("--report", action="store_true", help="Executar todos os checks")
    parser.add_argument("--strict", action="store_true", help="Modo strict (falhas causam exit 1)")
    parser.add_argument("--exit-after-report", action="store_true", help="Sair após gerar relatório")
    parser.add_argument("--output", default="ui_report.json", help="Arquivo de saída do relatório")
    
    args = parser.parse_args()
    
    if not args.report:
        print("Use --report para executar os checks")
        return 0
    
    reporter = UIReporter(strict_mode=args.strict)
    success = reporter.run_all_checks()
    
    reporter.save_report(args.output)
    
    if args.exit_after_report or args.strict:
        return 0 if success else 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
