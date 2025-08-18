"""
Sistema de Backup Automático para o Sistema de Recomendações
Gerencia backups automáticos do banco de dados com retenção e notificações
"""
import os
import sys
import json
import shutil
import sqlite3
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseBackupSystem:
    """Sistema de backup automático para banco de dados"""
    
    def __init__(self, config_path: str = "config_producao.env"):
        self.config = self._load_config(config_path)
        self.backup_path = Path(self.config.get('DATABASE_BACKUP_PATH', './backups/'))
        self.retention_days = int(self.config.get('DATABASE_BACKUP_RETENTION_DAYS', 30))
        self.database_url = self.config.get('DATABASE_URL', 'sqlite:///production.db')
        
        # Cria diretório de backup se não existir
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Configurações de notificação
        self.alert_email = self.config.get('ALERT_EMAIL', '')
        self.slack_webhook = self.config.get('SLACK_WEBHOOK_URL', '')
        
        # Estatísticas de backup
        self.backup_stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'last_backup': None,
            'last_backup_size': 0,
            'total_backup_size': 0
        }
        
        # Carrega estatísticas salvas
        self._load_backup_stats()
    
    def _load_config(self, config_path: str) -> Dict[str, str]:
        """Carrega configurações do arquivo"""
        config = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
        
        return config
    
    def _load_backup_stats(self):
        """Carrega estatísticas de backup salvas"""
        stats_file = self.backup_path / 'backup_stats.json'
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    saved_stats = json.load(f)
                    self.backup_stats.update(saved_stats)
        except Exception as e:
                logger.error(f"Erro ao carregar estatísticas: {e}")
    
    def _save_backup_stats(self):
        """Salva estatísticas de backup"""
        stats_file = self.backup_path / 'backup_stats.json'
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar estatísticas: {e}")
    
    def create_backup(self) -> Tuple[bool, str, Optional[Path]]:
        """
        Cria backup do banco de dados
        
        Returns:
            Tuple[bool, str, Optional[Path]]: (sucesso, mensagem, caminho_do_backup)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Determina tipo de banco e método de backup
            if 'sqlite' in self.database_url.lower():
                return self._backup_sqlite(timestamp)
            elif 'postgresql' in self.database_url.lower():
                return self._backup_postgresql(timestamp)
            elif 'mysql' in self.database_url.lower():
                return self._backup_mysql(timestamp)
            else:
                return False, f"Tipo de banco não suportado: {self.database_url}", None
            
        except Exception as e:
            error_msg = f"Erro ao criar backup: {e}"
            logger.error(error_msg)
            self._send_backup_alert("❌ Falha no Backup", error_msg)
            return False, error_msg, None
    
    def _backup_sqlite(self, timestamp: str) -> Tuple[bool, str, Optional[Path]]:
        """Backup para banco SQLite"""
        try:
            # Extrai caminho do banco da URL
            db_path = self.database_url.replace('sqlite:///', '')
            if not os.path.exists(db_path):
                return False, f"Banco SQLite não encontrado: {db_path}", None
            
            # Nome do arquivo de backup
            backup_filename = f"backup_sqlite_{timestamp}.db"
            backup_file = self.backup_path / backup_filename
            
            # Cria backup
            shutil.copy2(db_path, backup_file)
            
            # Verifica integridade do backup
            if not self._verify_sqlite_backup(backup_file):
                backup_file.unlink()  # Remove backup corrompido
                return False, "Backup corrompido - verificação falhou", None
            
            # Atualiza estatísticas
            backup_size = backup_file.stat().st_size
            self._update_backup_stats(True, backup_size)
            
            success_msg = f"Backup SQLite criado com sucesso: {backup_filename} ({self._format_size(backup_size)})"
            logger.info(success_msg)
            
            # Envia notificação de sucesso
            self._send_backup_alert("✅ Backup Concluído", success_msg)
            
            return True, success_msg, backup_file
            
        except Exception as e:
            error_msg = f"Erro no backup SQLite: {e}"
            logger.error(error_msg)
            self._update_backup_stats(False, 0)
            return False, error_msg, None
    
    def _backup_postgresql(self, timestamp: str) -> Tuple[bool, str, Optional[Path]]:
        """Backup para banco PostgreSQL"""
        try:
            # Extrai informações de conexão da URL
            # Formato: postgresql://user:password@host:port/database
            db_url = self.database_url.replace('postgresql://', '')
            
            if '@' in db_url:
                credentials, host_db = db_url.split('@', 1)
                if ':' in credentials:
                    user, password = credentials.split(':', 1)
                else:
                    user, password = credentials, ''
                
                if ':' in host_db:
                    host_port, database = host_db.rsplit('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                    else:
                        host, port = host_port, '5432'
                else:
                    host, port, database = host_db, '5432', host_db
            else:
                return False, "Formato de URL PostgreSQL inválido", None
            
            # Nome do arquivo de backup
            backup_filename = f"backup_postgresql_{timestamp}.sql"
            backup_file = self.backup_path / backup_filename
            
            # Comando pg_dump
            import subprocess
            cmd = [
                'pg_dump',
                f'--host={host}',
                f'--port={port}',
                f'--username={user}',
                f'--dbname={database}',
                '--no-password',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f'--file={backup_file}'
            ]
            
            # Define variável de ambiente para senha
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # Executa backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, f"Erro no pg_dump: {result.stderr}", None
            
            # Verifica se arquivo foi criado
            if not backup_file.exists():
                return False, "Arquivo de backup não foi criado", None
            
            # Atualiza estatísticas
            backup_size = backup_file.stat().st_size
            self._update_backup_stats(True, backup_size)
            
            success_msg = f"Backup PostgreSQL criado com sucesso: {backup_filename} ({self._format_size(backup_size)})"
            logger.info(success_msg)
            
            # Envia notificação de sucesso
            self._send_backup_alert("✅ Backup Concluído", success_msg)
            
            return True, success_msg, backup_file
            
        except Exception as e:
            error_msg = f"Erro no backup PostgreSQL: {e}"
            logger.error(error_msg)
            self._update_backup_stats(False, 0)
            return False, error_msg, None
    
    def _backup_mysql(self, timestamp: str) -> Tuple[bool, str, Optional[Path]]:
        """Backup para banco MySQL"""
        try:
            # Extrai informações de conexão da URL
            # Formato: mysql://user:password@host:port/database
            db_url = self.database_url.replace('mysql://', '')
            
            if '@' in db_url:
                credentials, host_db = db_url.split('@', 1)
                if ':' in credentials:
                    user, password = credentials.split(':', 1)
                else:
                    user, password = credentials, ''
                
                if ':' in host_db:
                    host_port, database = host_db.rsplit('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                    else:
                        host, port = host_port, '3306'
                else:
                    host, port, database = host_db, '3306', host_db
            else:
                return False, "Formato de URL MySQL inválido", None
            
            # Nome do arquivo de backup
            backup_filename = f"backup_mysql_{timestamp}.sql"
            backup_file = self.backup_path / backup_filename
            
            # Comando mysqldump
            import subprocess
            cmd = [
                'mysqldump',
                f'--host={host}',
                f'--port={port}',
                f'--user={user}',
                f'--password={password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                '--events',
                database
            ]
            
            # Executa backup
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return False, f"Erro no mysqldump: {result.stderr}", None
            
            # Verifica se arquivo foi criado
            if not backup_file.exists():
                return False, "Arquivo de backup não foi criado", None
            
            # Atualiza estatísticas
            backup_size = backup_file.stat().st_size
            self._update_backup_stats(True, backup_size)
            
            success_msg = f"Backup MySQL criado com sucesso: {backup_filename} ({self._format_size(backup_size)})"
            logger.info(success_msg)
            
            # Envia notificação de sucesso
            self._send_backup_alert("✅ Backup Concluído", success_msg)
            
            return True, success_msg, backup_file
            
        except Exception as e:
            error_msg = f"Erro no backup MySQL: {e}"
            logger.error(error_msg)
            self._update_backup_stats(False, 0)
            return False, error_msg, None
    
    def _verify_sqlite_backup(self, backup_file: Path) -> bool:
        """Verifica integridade de backup SQLite"""
        try:
            # Tenta abrir o backup
            conn = sqlite3.connect(str(backup_file))
            cursor = conn.cursor()
            
            # Executa consulta simples para verificar integridade
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            conn.close()
            
            # Se conseguiu listar tabelas, o backup está íntegro
            return len(tables) > 0
            
        except Exception as e:
            logger.error(f"Verificação de backup falhou: {e}")
            return False
    
    def _update_backup_stats(self, success: bool, backup_size: int):
        """Atualiza estatísticas de backup"""
        self.backup_stats['total_backups'] += 1
        
        if success:
            self.backup_stats['successful_backups'] += 1
            self.backup_stats['last_backup'] = datetime.now().isoformat()
            self.backup_stats['last_backup_size'] = backup_size
            self.backup_stats['total_backup_size'] += backup_size
        else:
            self.backup_stats['failed_backups'] += 1
        
        # Salva estatísticas
        self._save_backup_stats()
    
    def cleanup_old_backups(self) -> Tuple[int, int]:
        """
        Remove backups antigos baseado na política de retenção
        
        Returns:
            Tuple[int, int]: (backups_removidos, espaço_liberado_mb)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            freed_space = 0
            
            # Lista todos os arquivos de backup
            backup_files = list(self.backup_path.glob('backup_*'))
            
            for backup_file in backup_files:
                try:
                    # Obtém data de modificação
                    mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        # Calcula espaço que será liberado
                        file_size = backup_file.stat().st_size
                        freed_space += file_size
                        
                        # Remove arquivo
                        backup_file.unlink()
                        removed_count += 1
                        
                        logger.info(f"🗑️ Backup antigo removido: {backup_file.name}")
                        
                except Exception as e:
                    logger.error(f"Erro ao remover backup {backup_file.name}: {e}")
            
            if removed_count > 0:
                freed_mb = freed_space / (1024 * 1024)
                logger.info(f"🧹 Limpeza concluída: {removed_count} backups removidos, {freed_mb:.2f} MB liberados")
                
                # Envia notificação de limpeza
                self._send_backup_alert("🧹 Limpeza de Backups", 
                                      f"{removed_count} backups antigos removidos\n{freed_mb:.2f} MB liberados")
            
            return removed_count, freed_space
            
        except Exception as e:
            logger.error(f"Erro na limpeza de backups: {e}")
            return 0, 0
    
    def get_backup_status(self) -> Dict[str, any]:
        """Retorna status atual dos backups"""
        try:
            # Lista backups existentes
            backup_files = list(self.backup_path.glob('backup_*'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Calcula espaço total usado
            total_size = sum(f.stat().st_size for f in backup_files)
            
            # Informações sobre backups
            backups_info = []
            for backup_file in backup_files[:10]:  # Últimos 10 backups
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                size = backup_file.stat().st_size
                
                backups_info.append({
                    'filename': backup_file.name,
                    'size': size,
                    'size_formatted': self._format_size(size),
                    'date': mtime.isoformat(),
                    'age_days': (datetime.now() - mtime).days
                })
            
            return {
                'status': 'operational',
                'total_backups': len(backup_files),
                'total_size': total_size,
                'total_size_formatted': self._format_size(total_size),
                'retention_days': self.retention_days,
                'last_backup': self.backup_stats.get('last_backup'),
                'backup_success_rate': self._calculate_success_rate(),
                'recent_backups': backups_info,
                'stats': self.backup_stats
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status de backup: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_success_rate(self) -> float:
        """Calcula taxa de sucesso dos backups"""
        total = self.backup_stats['total_backups']
        if total == 0:
            return 0.0
        
        successful = self.backup_stats['successful_backups']
        return (successful / total) * 100
    
    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def _send_backup_alert(self, title: str, message: str):
        """Envia alerta de backup via email e/ou Slack"""
        try:
            # Email
            if self.alert_email:
                self._send_email_alert(title, message)
            
            # Slack
            if self.slack_webhook:
                self._send_slack_alert(title, message)
                
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")
    
    def _send_email_alert(self, title: str, message: str):
        """Envia alerta por email"""
        try:
            # Configurações de email (simples para demonstração)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = os.getenv('ALERT_EMAIL_FROM', '')
            sender_password = os.getenv('ALERT_EMAIL_PASSWORD', '')
            
            if not sender_email or not sender_password:
                logger.warning("Credenciais de email não configuradas")
                return
            
            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = self.alert_email
            msg['Subject'] = f"[Sistema de Recomendações] {title}"
            
            body = f"""
            Sistema de Recomendações - Backup
            
            {title}
            
            {message}
            
            Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            
            ---
            Sistema de Backup Automático
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Envia email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, self.alert_email, text)
            server.quit()
            
            logger.info(f"📧 Alerta por email enviado para {self.alert_email}")
                        
                    except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
    
    def _send_slack_alert(self, title: str, message: str):
        """Envia alerta para Slack"""
        try:
            payload = {
                "text": f"*{title}*\n{message}",
                "username": "Sistema de Backup",
                "icon_emoji": ":floppy_disk:"
            }
            
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("📱 Alerta enviado para Slack")
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta Slack: {e}")
    
    def start_scheduled_backup(self, interval_hours: int = 24):
        """Inicia backup agendado"""
        try:
            logger.info(f"⏰ Iniciando backup agendado a cada {interval_hours} horas")
            
            # Agenda backup
            schedule.every(interval_hours).hours.do(self.create_backup)
            
            # Agenda limpeza (diária)
            schedule.every().day.at("03:00").do(self.cleanup_old_backups)
            
            # Loop principal
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
                
        except KeyboardInterrupt:
            logger.info("🛑 Backup agendado interrompido")
                except Exception as e:
            logger.error(f"Erro no backup agendado: {e}")
    
    def start_backup_service(self):
        """Inicia serviço de backup em thread separada"""
        try:
            backup_thread = threading.Thread(
                target=self.start_scheduled_backup,
                daemon=True
            )
            backup_thread.start()
            
            logger.info("🚀 Serviço de backup iniciado em background")
            return backup_thread
            
        except Exception as e:
            logger.error(f"Erro ao iniciar serviço de backup: {e}")
            return None


def main():
    """Função principal para teste do sistema de backup"""
    print("💾 Sistema de Backup Automático")
    print("=" * 40)
    
    backup_system = DatabaseBackupSystem()
    
    # Exibe status atual
    print("\n📊 Status dos Backups:")
    status = backup_system.get_backup_status()
    
    if status['status'] == 'operational':
        print(f"   Total de backups: {status['total_backups']}")
        print(f"   Espaço usado: {status['total_size_formatted']}")
        print(f"   Taxa de sucesso: {status['backup_success_rate']:.1f}%")
        
        if status['last_backup']:
            print(f"   Último backup: {status['last_backup']}")
            else:
        print(f"   Status: {status['status']}")
        if 'error' in status:
            print(f"   Erro: {status['error']}")
    
    # Pergunta se deve criar backup manual
    response = input("\n❓ Deseja criar um backup manual agora? (s/N): ")
    if response.lower() in ['s', 'sim', 'y', 'yes']:
        print("\n🔄 Criando backup manual...")
        success, message, backup_file = backup_system.create_backup()
        
        if success:
            print(f"✅ {message}")
            else:
            print(f"❌ {message}")
    
    # Pergunta se deve iniciar serviço automático
    response = input("\n❓ Deseja iniciar o serviço de backup automático? (s/N): ")
    if response.lower() in ['s', 'sim', 'y', 'yes']:
        print("\n🚀 Iniciando serviço de backup automático...")
        backup_system.start_backup_service()
        
        try:
            # Mantém programa rodando
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Serviço interrompido pelo usuário")


if __name__ == "__main__":
    main()
