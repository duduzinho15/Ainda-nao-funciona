#!/usr/bin/env python3
"""
Script de Refatoração do Garimpeiro Geek
Move arquivos para nova estrutura src/ e atualiza imports automaticamente
"""

import os
import re
import shutil
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging

class RefactorEngine:
    """Motor de refatoração para reorganizar o projeto"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.import_map = {}
        self.moved_files = []
        self.updated_files = []
        self.shims_created = []
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("refactor_engine")
        
        # Mapeamento de arquivos para nova estrutura
        self.file_mapping = {
            # Scrapers
            "amazon_scraper.py": "src/scrapers/amazon/amazon_scraper.py",
            "amazon_playwright_scraper.py": "src/scrapers/amazon/amazon_playwright_scraper.py",
            "shopee_scraper.py": "src/scrapers/shopee/shopee_scraper.py",
            "aliexpress_scraper.py": "src/scrapers/aliexpress/aliexpress_scraper.py",
            "magalu_scraper.py": "src/scrapers/magalu/magalu_scraper.py",
            "kabum_scraper.py": "src/scrapers/kabum/kabum_scraper.py",
            "promobit_scraper.py": "src/scrapers/promobit/promobit_scraper.py",
            "submarino_scraper.py": "src/scrapers/submarino/submarino_scraper.py",
            "americanas_scraper.py": "src/scrapers/americanas/americanas_scraper.py",
            "meupc_scraper.py": "src/scrapers/meupc/meupc_scraper.py",
            "casas_bahia_scraper.py": "src/scrapers/casas_bahia/casas_bahia_scraper.py",
            "fast_shop_scraper.py": "src/scrapers/fast_shop/fast_shop_scraper.py",
            "ricardo_eletro_scraper.py": "src/scrapers/ricardo_eletro/ricardo_eletro_scraper.py",
            
            # Providers/APIs
            "mercadolivre_api.py": "src/providers/mercadolivre/mercadolivre_api.py",
            "shopee_api.py": "src/providers/shopee_api/shopee_api.py",
            "aliexpress_api.py": "src/providers/aliexpress_api/aliexpress_api.py",
            
            # Core modules
            "scraper_registry.py": "src/core/scraper_registry.py",
            "normalize.py": "src/core/normalize.py",
            "csv_exporter.py": "src/core/csv_exporter.py",
            "live_logs.py": "src/core/live_logs.py",
            "data_service.py": "src/core/data_service.py",
            "rate_limiter.py": "src/core/rate_limiter.py",
            "logging_setup.py": "src/core/logging_setup.py",
            "utils.py": "src/core/utils.py",
            "models.py": "src/core/models.py",
            "settings.py": "src/core/settings.py",
            "storage.py": "src/core/storage.py",
            "database.py": "src/core/database.py",
            "metrics.py": "src/core/metrics.py",
            "affiliate_converter.py": "src/core/affiliate_converter.py",
            
            # Dashboard e UI
            "dashboard.py": "src/app/dashboard/dashboard.py",
            "ui_reporter.py": "src/diagnostics/ui_reporter.py",
            "verify_snapshot.py": "src/diagnostics/verify_snapshot.py",
            "smoke_sources.py": "src/diagnostics/smoke_sources.py",
            
            # Bot e notificações
            "telegram_bot.py": "src/app/bot/telegram_bot.py",
            "geek_auto_poster.py": "src/posting/geek_auto_poster.py",
            "notification_system.py": "src/posting/notification_system.py",
            
            # Recomendações
            "price_comparator.py": "src/recommender/price_comparator.py",
            "recommender.py": "src/recommender/recommender.py",
            "rules.py": "src/recommender/rules.py",
            
            # Base classes
            "base_scraper.py": "src/scrapers/base_scraper.py",
            "base_api.py": "src/providers/base_api.py",
            
            # Testes
            "test_core_modules.py": "src/tests/unit/test_core_modules.py",
            "test_scrapers.py": "src/tests/integration/test_scrapers.py",
        }
        
        # Mapeamento de imports
        self.import_mapping = {
            # Core modules
            "core.scraper_registry": "src.core.scraper_registry",
            "core.normalize": "src.core.normalize",
            "core.csv_exporter": "src.core.csv_exporter",
            "core.live_logs": "src.core.live_logs",
            "core.data_service": "src.core.data_service",
            "core.rate_limiter": "src.core.rate_limiter",
            "core.logging_setup": "src.core.logging_setup",
            "core.utils": "src.core.utils",
            "core.models": "src.core.models",
            "core.settings": "src.core.settings",
            "core.storage": "src.core.storage",
            "core.database": "src.core.database",
            "core.metrics": "src.core.metrics",
            "core.affiliate_converter": "src.core.affiliate_converter",
            
            # Scrapers
            "amazon_scraper": "src.scrapers.amazon.amazon_scraper",
            "shopee_scraper": "src.scrapers.shopee.shopee_scraper",
            "aliexpress_scraper": "src.scrapers.aliexpress.aliexpress_scraper",
            "magalu_scraper": "src.scrapers.magalu.magalu_scraper",
            "kabum_scraper": "src.scrapers.kabum.kabum_scraper",
            "promobit_scraper": "src.scrapers.promobit.promobit_scraper",
            "submarino_scraper": "src.scrapers.submarino.submarino_scraper",
            "americanas_scraper": "src.scrapers.americanas.americanas_scraper",
            "meupc_scraper": "src.scrapers.meupc.meupc_scraper",
            "casas_bahia_scraper": "src.scrapers.casas_bahia.casas_bahia_scraper",
            "fast_shop_scraper": "src.scrapers.fast_shop.fast_shop_scraper",
            "ricardo_eletro_scraper": "src.scrapers.ricardo_eletro.ricardo_eletro_scraper",
            
            # Providers
            "providers.mercadolivre_api": "src.providers.mercadolivre.mercadolivre_api",
            "providers.shopee_api": "src.providers.shopee_api.shopee_api",
            "providers.aliexpress_api": "src.providers.aliexpress_api.aliexpress_api",
            
            # App modules
            "app.dashboard": "src.app.dashboard.dashboard",
            "telegram.bot": "src.app.bot.telegram_bot",
            
            # Diagnostics
            "diagnostics.ui_reporter": "src.diagnostics.ui_reporter",
            "diagnostics.verify_snapshot": "src.diagnostics.verify_snapshot",
            "diagnostics.smoke_sources": "src.diagnostics.smoke_sources",
            
            # Posting
            "posting.geek_auto_poster": "src.posting.geek_auto_poster",
            "posting.notification_system": "src.posting.notification_system",
            
            # Recommender
            "recommender.price_comparator": "src.recommender.price_comparator",
            "recommender.recommender": "src.recommender.recommender",
            "recommender.rules": "src.recommender.rules",
        }
    
    def scan_repository(self) -> Dict[str, List[str]]:
        """Escaneia o repositório e encontra todos os arquivos Python"""
        python_files = []
        other_files = []
        
        for root, dirs, files in os.walk(self.repo_root):
            # Pular diretórios que não devem ser escaneados
            dirs[:] = [d for d in dirs if d not in [
                '__pycache__', '.git', '.venv', 'venv', 'node_modules',
                'build', 'dist', '.pytest_cache', '.mypy_cache'
            ]]
            
            for file in files:
                file_path = Path(root) / file
                if file.endswith('.py'):
                    python_files.append(str(file_path))
                else:
                    other_files.append(str(file_path))
        
        return {
            'python_files': python_files,
            'other_files': other_files
        }
    
    def generate_import_map(self) -> Dict[str, str]:
        """Gera mapa de imports baseado na estrutura atual"""
        import_map = {}
        
        # Escanear repositório
        files = self.scan_repository()
        
        for python_file in files['python_files']:
            file_path = Path(python_file)
            file_name = file_path.name
            
            # Verificar se o arquivo está no mapeamento
            if file_name in self.file_mapping:
                old_path = str(file_path.relative_to(self.repo_root))
                new_path = self.file_mapping[file_name]
                import_map[old_path] = new_path
                
                # Adicionar mapeamento de imports
                old_module = old_path.replace('/', '.').replace('.py', '')
                new_module = new_path.replace('/', '.').replace('.py', '')
                self.import_mapping[old_module] = new_module
        
        return import_map
    
    def create_directories(self):
        """Cria diretórios necessários para a nova estrutura"""
        directories = set()
        
        for new_path in self.file_mapping.values():
            dir_path = Path(new_path).parent
            directories.add(dir_path)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✅ Diretório criado: {directory}")
    
    def move_files(self, dry_run: bool = True) -> List[Tuple[str, str]]:
        """Move arquivos para nova estrutura"""
        moved_files = []
        
        for old_path, new_path in self.file_mapping.items():
            # Procurar arquivo no repositório
            found_files = list(self.repo_root.rglob(old_path))
            
            if found_files:
                source_file = found_files[0]
                target_file = self.repo_root / new_path
                
                if dry_run:
                    self.logger.info(f"🔄 DRY-RUN: {source_file} → {target_file}")
                    moved_files.append((str(source_file), str(target_file)))
                else:
                    try:
                        # Criar diretório de destino se não existir
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Mover arquivo
                        shutil.move(str(source_file), str(target_file))
                        self.logger.info(f"✅ Movido: {source_file} → {target_file}")
                        moved_files.append((str(source_file), str(target_file)))
                        
                    except Exception as e:
                        self.logger.error(f"❌ Erro ao mover {source_file}: {e}")
            else:
                self.logger.warning(f"⚠️ Arquivo não encontrado: {old_path}")
        
        return moved_files
    
    def update_imports_in_file(self, file_path: Path, dry_run: bool = True) -> bool:
        """Atualiza imports em um arquivo Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            updated = False
            
            # Atualizar imports
            for old_import, new_import in self.import_mapping.items():
                # Padrão: from old_import import ...
                pattern1 = rf'from\s+{re.escape(old_import)}\s+import'
                replacement1 = f'from {new_import} import'
                
                if re.search(pattern1, content):
                    content = re.sub(pattern1, replacement1, content)
                    updated = True
                
                # Padrão: import old_import
                pattern2 = rf'import\s+{re.escape(old_import)}'
                replacement2 = f'import {new_import}'
                
                if re.search(pattern2, content):
                    content = re.sub(pattern2, replacement2, content)
                    updated = True
            
            if updated:
                if dry_run:
                    self.logger.info(f"🔄 DRY-RUN: Imports atualizados em {file_path}")
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"✅ Imports atualizados em {file_path}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar imports em {file_path}: {e}")
            return False
    
    def update_all_imports(self, dry_run: bool = True) -> int:
        """Atualiza imports em todos os arquivos Python"""
        updated_count = 0
        
        # Escanear repositório
        files = self.scan_repository()
        
        for python_file in files['python_files']:
            file_path = Path(python_file)
            
            # Pular arquivos que foram movidos
            if any(str(file_path).endswith(new_path) for new_path in self.file_mapping.values()):
                continue
            
            if self.update_imports_in_file(file_path, dry_run):
                updated_count += 1
        
        return updated_count
    
    def create_shims(self, dry_run: bool = True) -> List[str]:
        """Cria shims de compatibilidade para módulos legados"""
        shims_created = []
        
        # Módulos que precisam de shims
        modules_needing_shims = [
            "amazon_scraper",
            "shopee_scraper", 
            "aliexpress_scraper",
            "magalu_scraper",
            "kabum_scraper",
            "promobit_scraper",
            "submarino_scraper",
            "americanas_scraper",
            "meupc_scraper",
            "casas_bahia_scraper",
            "fast_shop_scraper",
            "ricardo_eletro_scraper",
            "mercadolivre_api",
            "shopee_api",
            "aliexpress_api",
        ]
        
        for module in modules_needing_shims:
            shim_file = self.repo_root / f"{module}.py"
            
            if dry_run:
                self.logger.info(f"🔄 DRY-RUN: Criando shim {shim_file}")
                shims_created.append(str(shim_file))
            else:
                try:
                    # Determinar novo caminho
                    new_path = None
                    for old_name, new_name in self.file_mapping.items():
                        if old_name.startswith(module):
                            new_path = new_name.replace('.py', '').replace('/', '.')
                            break
                    
                    if new_path:
                        shim_content = f'''# shim temporário — será removido depois
import warnings
warnings.warn("Use '{new_path}' instead of '{module}'", DeprecationWarning)

try:
    from {new_path} import *
except ImportError:
    # Fallback para compatibilidade
    pass
'''
                        
                        with open(shim_file, 'w', encoding='utf-8') as f:
                            f.write(shim_content)
                        
                        self.logger.info(f"✅ Shim criado: {shim_file}")
                        shims_created.append(str(shim_file))
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao criar shim {module}: {e}")
        
        return shims_created
    
    def move_other_files(self, dry_run: bool = True) -> List[Tuple[str, str]]:
        """Move outros arquivos para pastas apropriadas"""
        moved_files = []
        
        # Mapeamento de extensões para pastas
        extension_mapping = {
            '.log': 'logs/',
            '.db': 'data/',
            '.sql': 'data/',
            '.html': 'samples/html/',
            '.json': 'samples/json/',
            '.csv': 'exports/',
            '.env': 'config/',
            '.txt': 'config/',
            '.ps1': 'scripts/',
            '.bat': 'scripts/',
            '.yml': 'config/',
            '.yaml': 'config/',
        }
        
        # Mapeamento de nomes específicos
        name_mapping = {
            'requirements.txt': 'config/',
            'scrapers.json': 'config/',
            'config.py': 'config/',
            'env_example.txt': 'config/',
            'SETUP_GITHUB.md': 'config/',
            'README.md': './',  # Manter na raiz
            'pyproject.toml': './',  # Manter na raiz
            'Makefile': './',  # Manter na raiz
            '.gitignore': './',  # Manter na raiz
        }
        
        # Escanear repositório
        files = self.scan_repository()
        
        for file_path in files['other_files']:
            path_obj = Path(file_path)
            file_name = path_obj.name
            
            # Verificar mapeamento por nome
            if file_name in name_mapping:
                target_dir = name_mapping[file_name]
            else:
                # Verificar mapeamento por extensão
                target_dir = extension_mapping.get(path_obj.suffix, '_archive/')
            
            # Pular arquivos que já estão no lugar certo
            if str(path_obj).startswith(target_dir):
                continue
            
            target_path = self.repo_root / target_dir / file_name
            
            if dry_run:
                self.logger.info(f"🔄 DRY-RUN: {path_obj} → {target_path}")
                moved_files.append((str(path_obj), str(target_path)))
            else:
                try:
                    # Criar diretório de destino
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Mover arquivo
                    shutil.move(str(path_obj), str(target_path))
                    self.logger.info(f"✅ Movido: {path_obj} → {target_path}")
                    moved_files.append((str(path_obj), str(target_path)))
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao mover {path_obj}: {e}")
        
        return moved_files
    
    def create_init_files(self, dry_run: bool = True):
        """Cria arquivos __init__.py necessários"""
        init_locations = [
            "src/__init__.py",
            "src/app/__init__.py",
            "src/app/dashboard/__init__.py",
            "src/app/bot/__init__.py",
            "src/core/__init__.py",
            "src/scrapers/__init__.py",
            "src/providers/__init__.py",
            "src/recommender/__init__.py",
            "src/posting/__init__.py",
            "src/diagnostics/__init__.py",
            "src/tests/__init__.py",
            "src/tests/unit/__init__.py",
            "src/tests/integration/__init__.py",
        ]
        
        for init_file in init_locations:
            init_path = self.repo_root / init_file
            
            if dry_run:
                self.logger.info(f"🔄 DRY-RUN: Criando {init_file}")
            else:
                try:
                    init_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Conteúdo básico do __init__.py
                    content = f'''"""
{init_path.parent.name} package for Garimpeiro Geek
Sistema de Recomendações de Ofertas via Telegram
"""

__version__ = "1.0.0"
__author__ = "Garimpeiro Geek Team"
'''
                    
                    with open(init_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.logger.info(f"✅ __init__.py criado: {init_file}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao criar {init_file}: {e}")
    
    def generate_report(self, dry_run: bool = True) -> str:
        """Gera relatório da refatoração"""
        report = []
        report.append("# 📋 Relatório de Refatoração - Garimpeiro Geek")
        report.append("")
        report.append(f"**Modo:** {'DRY-RUN' if dry_run else 'APLICADO'}")
        report.append(f"**Data:** {Path().cwd()}")
        report.append("")
        
        # Resumo
        report.append("## 📊 Resumo")
        report.append(f"- Arquivos Python escaneados: {len(self.scan_repository()['python_files'])}")
        report.append(f"- Arquivos movidos: {len(self.moved_files)}")
        report.append(f"- Imports atualizados: {len(self.updated_files)}")
        report.append(f"- Shims criados: {len(self.shims_created)}")
        report.append("")
        
        # Arquivos movidos
        if self.moved_files:
            report.append("## 📁 Arquivos Movidos")
            for old_path, new_path in self.moved_files:
                report.append(f"- `{old_path}` → `{new_path}`")
            report.append("")
        
        # Imports atualizados
        if self.updated_files:
            report.append("## 🔄 Imports Atualizados")
            for file_path in self.updated_files:
                report.append(f"- `{file_path}`")
            report.append("")
        
        # Shims criados
        if self.shims_created:
            report.append("## 🔗 Shims de Compatibilidade")
            report.append("**⚠️ ATENÇÃO:** Estes shims são temporários e serão removidos!")
            for shim in self.shims_created:
                report.append(f"- `{shim}`")
            report.append("")
        
        # Mapeamento de imports
        report.append("## 🗺️ Mapeamento de Imports")
        for old_import, new_import in self.import_mapping.items():
            report.append(f"- `{old_import}` → `{new_import}`")
        report.append("")
        
        # Próximos passos
        report.append("## 🚀 Próximos Passos")
        if dry_run:
            report.append("1. ✅ Revisar o plano de refatoração")
            report.append("2. 🔄 Executar `make refactor-apply` para aplicar")
            report.append("3. 🧪 Executar testes para verificar funcionamento")
            report.append("4. 📊 Executar UI Reporter para verificar dashboard")
        else:
            report.append("1. ✅ Refatoração aplicada com sucesso!")
            report.append("2. 🧪 Executar `make tests` para verificar funcionamento")
            report.append("3. 📊 Executar `make ui-ci` para verificar dashboard")
            report.append("4. 🔍 Verificar se não há imports não resolvidos")
            report.append("5. 🗑️ Remover shims temporários após estabilização")
        
        return "\n".join(report)
    
    def run_refactor(self, dry_run: bool = True):
        """Executa a refatoração completa"""
        self.logger.info(f"🚀 Iniciando refatoração {'(DRY-RUN)' if dry_run else '(APLICAÇÃO)'}")
        
        # 1. Gerar mapa de imports
        self.logger.info("📋 Gerando mapa de imports...")
        self.import_map = self.generate_import_map()
        
        # 2. Criar diretórios
        self.logger.info("📁 Criando diretórios...")
        self.create_directories()
        
        # 3. Mover arquivos Python
        self.logger.info("🔄 Movendo arquivos Python...")
        self.moved_files = self.move_files(dry_run)
        
        # 4. Mover outros arquivos
        self.logger.info("📦 Movendo outros arquivos...")
        other_moved = self.move_other_files(dry_run)
        self.moved_files.extend(other_moved)
        
        # 5. Atualizar imports
        self.logger.info("🔗 Atualizando imports...")
        updated_count = self.update_all_imports(dry_run)
        
        # 6. Criar shims
        self.logger.info("🔗 Criando shims de compatibilidade...")
        self.shims_created = self.create_shims(dry_run)
        
        # 7. Criar arquivos __init__.py
        self.logger.info("📝 Criando arquivos __init__.py...")
        self.create_init_files(dry_run)
        
        # 8. Gerar relatório
        self.logger.info("📊 Gerando relatório...")
        report = self.generate_report(dry_run)
        
        # Salvar relatório
        report_file = self.repo_root / "tools/refactor/report.md"
        if not dry_run:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"✅ Relatório salvo: {report_file}")
        
        # Salvar import map
        import_map_file = self.repo_root / "tools/refactor/import_map.json"
        if not dry_run:
            with open(import_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.import_map, f, indent=2, default=str)
            self.logger.info(f"✅ Import map salvo: {import_map_file}")
        
        # Mostrar resumo
        print("\n" + "="*80)
        print(report)
        print("="*80)
        
        if dry_run:
            self.logger.info("✅ DRY-RUN concluído. Execute com --apply para aplicar as mudanças.")
        else:
            self.logger.info("🎉 Refatoração aplicada com sucesso!")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Refatoração do Garimpeiro Geek")
    parser.add_argument("--dry-run", action="store_true", default=True, 
                       help="Executar em modo dry-run (padrão)")
    parser.add_argument("--apply", action="store_true", 
                       help="Aplicar refatoração (mover arquivos)")
    parser.add_argument("--repo-root", type=str, default=".", 
                       help="Diretório raiz do repositório")
    
    args = parser.parse_args()
    
    # Determinar se é dry-run
    dry_run = not args.apply
    
    # Configurar diretório raiz
    repo_root = Path(args.repo_root).resolve()
    
    if not repo_root.exists():
        print(f"❌ Diretório não encontrado: {repo_root}")
        return 1
    
    # Executar refatoração
    try:
        engine = RefactorEngine(repo_root)
        engine.run_refactor(dry_run)
        return 0
        
    except Exception as e:
        print(f"❌ Erro durante refatoração: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

