#!/usr/bin/env python3
"""
Script de Backup do Garimpeiro Geek
Faz backup automático dos dados e configurações
"""

import os
import shutil
import zipfile
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

class BackupManager:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("backup_manager")
        
        # Configurações de backup
        self.config = {
            "auto_backup": True,
            "backup_interval_hours": 24,
            "retention_days": 7,
            "compress_backups": True,
            "backup_database": True,
            "backup_logs": True,
            "backup_configs": True,
            "backup_exports": True
        }
        
        self.load_config()
    
    def load_config(self):
        """Carrega configurações do arquivo de configuração"""
        config_file = Path("config.py")
        if config_file.exists():
            try:
                # Importar configurações dinamicamente
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_file)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                if hasattr(config_module, 'BACKUP_CONFIG'):
                    self.config.update(config_module.BACKUP_CONFIG)
                    self.logger.info("Configurações de backup carregadas")
            except Exception as e:
                self.logger.warning(f"Erro ao carregar configurações: {e}")
    
    def should_create_backup(self) -> bool:
        """Verifica se deve criar um novo backup baseado no intervalo"""
        if not self.config["auto_backup"]:
            return False
        
        # Verificar último backup
        last_backup = self.get_last_backup_time()
        if not last_backup:
            return True
        
        # Calcular se passou tempo suficiente
        hours_since_last = (datetime.now() - last_backup).total_seconds() / 3600
        return hours_since_last >= self.config["backup_interval_hours"]
    
    def get_last_backup_time(self) -> datetime:
        """Obtém o timestamp do último backup"""
        backup_files = list(self.backup_dir.glob("backup_*.zip"))
        if not backup_files:
            return None
        
        # Ordenar por data de modificação
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backup_files[0]
        
        # Extrair timestamp do nome do arquivo
        try:
            timestamp_str = latest_backup.stem.replace("backup_", "")
            return datetime.fromisoformat(timestamp_str)
        except:
            return datetime.fromtimestamp(latest_backup.stat().st_mtime)
    
    def create_backup(self, description: str = "") -> str:
        """Cria um novo backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"
        
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        self.logger.info(f"Iniciando backup: {backup_name}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup do banco de dados
                if self.config["backup_database"]:
                    self._backup_database(zipf)
                
                # Backup dos logs
                if self.config["backup_logs"]:
                    self._backup_logs(zipf)
                
                # Backup das configurações
                if self.config["backup_configs"]:
                    self._backup_configs(zipf)
                
                # Backup das exportações
                if self.config["backup_exports"]:
                    self._backup_exports(zipf)
                
                # Backup das configurações do sistema
                self._backup_system_config(zipf)
            
            self.logger.info(f"Backup criado com sucesso: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def _backup_database(self, zipf: zipfile.ZipFile):
        """Faz backup do banco de dados"""
        db_files = [
            ".data/garimpeiro_geek.db",
            ".data/garimpeiro_geek.db-shm",
            ".data/garimpeiro_geek.db-wal"
        ]
        
        for db_file in db_files:
            if Path(db_file).exists():
                zipf.write(db_file, f"database/{Path(db_file).name}")
                self.logger.info(f"Backup do banco: {db_file}")
    
    def _backup_logs(self, zipf: zipfile.ZipFile):
        """Faz backup dos logs"""
        log_dirs = ["logs", ".data/logs"]
        
        for log_dir in log_dirs:
            log_path = Path(log_dir)
            if log_path.exists():
                for log_file in log_path.rglob("*.log"):
                    try:
                        zipf.write(log_file, f"logs/{log_file.relative_to(log_path)}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao fazer backup do log {log_file}: {e}")
        
        self.logger.info("Backup dos logs concluído")
    
    def _backup_configs(self, zipf: zipfile.ZipFile):
        """Faz backup das configurações"""
        config_files = [
            "config.py",
            ".env",
            "env_example.txt",
            "requirements.txt"
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                zipf.write(config_file, f"configs/{Path(config_file).name}")
        
        self.logger.info("Backup das configurações concluído")
    
    def _backup_exports(self, zipf: zipfile.ZipFile):
        """Faz backup das exportações"""
        export_dir = Path("exports")
        if export_dir.exists():
            for export_file in export_dir.rglob("*"):
                if export_file.is_file():
                    try:
                        zipf.write(export_file, f"exports/{export_file.relative_to(export_dir)}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao fazer backup da exportação {export_file}: {e}")
        
        self.logger.info("Backup das exportações concluído")
    
    def _backup_system_config(self, zipf: zipf):
        """Faz backup das configurações do sistema"""
        # Criar arquivo de metadados do backup
        metadata = {
            "backup_timestamp": datetime.now().isoformat(),
            "system_info": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.name,
                "current_directory": str(Path.cwd())
            },
            "backup_config": self.config,
            "files_backed_up": []
        }
        
        # Adicionar metadados ao ZIP
        zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
    
    def restore_backup(self, backup_path: str, target_dir: str = ".") -> bool:
        """Restaura um backup"""
        backup_file = Path(backup_path)
        if not backup_file.exists():
            self.logger.error(f"Arquivo de backup não encontrado: {backup_path}")
            return False
        
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)
        
        self.logger.info(f"Restaurando backup: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Verificar metadados
                if "backup_metadata.json" in zipf.namelist():
                    metadata = json.loads(zipf.read("backup_metadata.json"))
                    self.logger.info(f"Backup de: {metadata.get('backup_timestamp', 'Desconhecido')}")
                
                # Extrair arquivos
                zipf.extractall(target_path)
                
                self.logger.info(f"Backup restaurado com sucesso em: {target_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove backups antigos baseado na política de retenção"""
        if not self.config["retention_days"]:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config["retention_days"])
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                # Verificar data do arquivo
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"Backup antigo removido: {backup_file.name}")
            except Exception as e:
                self.logger.warning(f"Erro ao verificar backup {backup_file}: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"{deleted_count} backups antigos removidos")
    
    def list_backups(self) -> list:
        """Lista todos os backups disponíveis"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                stat = backup_file.stat()
                backup_info = {
                    "name": backup_file.name,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                }
                backups.append(backup_info)
            except Exception as e:
                self.logger.warning(f"Erro ao obter info do backup {backup_file}: {e}")
        
        # Ordenar por data de criação (mais recente primeiro)
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def get_backup_stats(self) -> dict:
        """Obtém estatísticas dos backups"""
        backups = self.list_backups()
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size_mb": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "average_size_mb": 0
            }
        
        total_size = sum(b["size_mb"] for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size, 2),
            "oldest_backup": min(b["created"] for b in backups),
            "newest_backup": max(b["created"] for b in backups),
            "average_size_mb": round(total_size / len(backups), 2)
        }

def main():
    """Função principal para execução do script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerenciador de Backup do Garimpeiro Geek")
    parser.add_argument("--create", action="store_true", help="Criar novo backup")
    parser.add_argument("--restore", type=str, help="Restaurar backup específico")
    parser.add_argument("--list", action="store_true", help="Listar backups disponíveis")
    parser.add_argument("--stats", action="store_true", help="Mostrar estatísticas dos backups")
    parser.add_argument("--cleanup", action="store_true", help="Limpar backups antigos")
    parser.add_argument("--auto", action="store_true", help="Verificar e criar backup automático")
    parser.add_argument("--description", type=str, help="Descrição do backup")
    
    args = parser.parse_args()
    
    backup_manager = BackupManager()
    
    try:
        if args.create:
            backup_path = backup_manager.create_backup(args.description)
            print(f"✅ Backup criado: {backup_path}")
        
        elif args.restore:
            if backup_manager.restore_backup(args.restore):
                print("✅ Backup restaurado com sucesso")
            else:
                print("❌ Falha ao restaurar backup")
        
        elif args.list:
            backups = backup_manager.list_backups()
            if backups:
                print("\n📦 Backups disponíveis:")
                for backup in backups:
                    print(f"  • {backup['name']} ({backup['size_mb']} MB) - {backup['created'].strftime('%d/%m/%Y %H:%M')}")
            else:
                print("📭 Nenhum backup encontrado")
        
        elif args.stats:
            stats = backup_manager.get_backup_stats()
            print("\n📊 Estatísticas dos Backups:")
            print(f"  • Total de backups: {stats['total_backups']}")
            print(f"  • Tamanho total: {stats['total_size_mb']} MB")
            print(f"  • Backup mais antigo: {stats['oldest_backup']}")
            print(f"  • Backup mais recente: {stats['newest_backup']}")
            print(f"  • Tamanho médio: {stats['average_size_mb']} MB")
        
        elif args.cleanup:
            backup_manager.cleanup_old_backups()
            print("✅ Limpeza de backups antigos concluída")
        
        elif args.auto:
            if backup_manager.should_create_backup():
                backup_path = backup_manager.create_backup("automático")
                print(f"✅ Backup automático criado: {backup_path}")
            else:
                print("⏰ Ainda não é hora de criar backup automático")
        
        else:
            # Modo interativo
            print("🔄 Gerenciador de Backup do Garimpeiro Geek")
            print("=" * 50)
            
            while True:
                print("\nEscolha uma opção:")
                print("1. Criar backup")
                print("2. Listar backups")
                print("3. Restaurar backup")
                print("4. Ver estatísticas")
                print("5. Limpar backups antigos")
                print("6. Backup automático")
                print("0. Sair")
                
                choice = input("\nOpção: ").strip()
                
                if choice == "1":
                    description = input("Descrição do backup (opcional): ").strip()
                    backup_path = backup_manager.create_backup(description)
                    print(f"✅ Backup criado: {backup_path}")
                
                elif choice == "2":
                    backups = backup_manager.list_backups()
                    if backups:
                        print("\n📦 Backups disponíveis:")
                        for backup in backups:
                            print(f"  • {backup['name']} ({backup['size_mb']} MB) - {backup['created'].strftime('%d/%m/%Y %H:%M')}")
                    else:
                        print("📭 Nenhum backup encontrado")
                
                elif choice == "3":
                    backups = backup_manager.list_backups()
                    if backups:
                        print("\nEscolha o backup para restaurar:")
                        for i, backup in enumerate(backups):
                            print(f"{i+1}. {backup['name']} ({backup['size_mb']} MB)")
                        
                        try:
                            idx = int(input("Número do backup: ")) - 1
                            if 0 <= idx < len(backups):
                                backup_file = backups[idx]['name']
                                if backup_manager.restore_backup(backup_file):
                                    print("✅ Backup restaurado com sucesso")
                                else:
                                    print("❌ Falha ao restaurar backup")
                            else:
                                print("❌ Opção inválida")
                        except ValueError:
                            print("❌ Entrada inválida")
                    else:
                        print("📭 Nenhum backup disponível para restaurar")
                
                elif choice == "4":
                    stats = backup_manager.get_backup_stats()
                    print("\n📊 Estatísticas dos Backups:")
                    print(f"  • Total de backups: {stats['total_backups']}")
                    print(f"  • Tamanho total: {stats['total_size_mb']} MB")
                    print(f"  • Backup mais antigo: {stats['oldest_backup']}")
                    print(f"  • Backup mais recente: {stats['newest_backup']}")
                    print(f"  • Tamanho médio: {stats['average_size_mb']} MB")
                
                elif choice == "5":
                    backup_manager.cleanup_old_backups()
                    print("✅ Limpeza de backups antigos concluída")
                
                elif choice == "6":
                    if backup_manager.should_create_backup():
                        backup_path = backup_manager.create_backup("automático")
                        print(f"✅ Backup automático criado: {backup_path}")
                    else:
                        print("⏰ Ainda não é hora de criar backup automático")
                
                elif choice == "0":
                    print("👋 Até logo!")
                    break
                
                else:
                    print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()

