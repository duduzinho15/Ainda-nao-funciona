"""
Sistema de logs em tempo real do Garimpeiro Geek
"""

import threading
from datetime import datetime
from typing import Any, Dict, List


class LiveLogReader:
    """Leitor de logs em tempo real"""

    def __init__(self, max_lines: int = 1000):
        self.max_lines = max_lines
        self.logs_buffer: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.is_running = False
        self.auto_scroll = True

    def add_log(self, nivel: str, mensagem: str, origem: str = "sistema"):
        """Adiciona um novo log ao buffer"""
        with self.lock:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "nivel": nivel,
                "mensagem": mensagem,
                "origem": origem,
            }

            self.logs_buffer.append(log_entry)

            # Manter apenas as últimas max_lines
            if len(self.logs_buffer) > self.max_lines:
                self.logs_buffer = self.logs_buffer[-self.max_lines :]

    def get_current_logs(self) -> List[Dict[str, Any]]:
        """Retorna os logs atuais"""
        with self.lock:
            return self.logs_buffer.copy()

    def get_logs_by_level(self, nivel: str) -> List[Dict[str, Any]]:
        """Retorna logs de um nível específico"""
        with self.lock:
            return [log for log in self.logs_buffer if log["nivel"] == nivel]

    def get_logs_by_origin(self, origem: str) -> List[Dict[str, Any]]:
        """Retorna logs de uma origem específica"""
        with self.lock:
            return [log for log in self.logs_buffer if log["origem"] == origem]

    def search_logs(self, query: str) -> List[Dict[str, Any]]:
        """Busca logs por texto"""
        with self.lock:
            query_lower = query.lower()
            return [
                log
                for log in self.logs_buffer
                if query_lower in log["mensagem"].lower()
                or query_lower in log["origem"].lower()
            ]

    def clear_buffer(self):
        """Limpa o buffer de logs"""
        with self.lock:
            self.logs_buffer.clear()

    def get_buffer_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do buffer"""
        with self.lock:
            if not self.logs_buffer:
                return {
                    "total_logs": 0,
                    "niveis": {},
                    "origens": {},
                    "primeiro_log": None,
                    "ultimo_log": None,
                }

            niveis = {}
            origens = {}

            for log in self.logs_buffer:
                nivel = log["nivel"]
                origem = log["origem"]

                niveis[nivel] = niveis.get(nivel, 0) + 1
                origens[origem] = origens.get(origem, 0) + 1

            return {
                "total_logs": len(self.logs_buffer),
                "niveis": niveis,
                "origens": origens,
                "primeiro_log": self.logs_buffer[0]["timestamp"],
                "ultimo_log": self.logs_buffer[-1]["timestamp"],
            }

    def export_logs(self, format: str = "json") -> str:
        """Exporta logs em diferentes formatos"""
        logs = self.get_current_logs()

        if format.lower() == "json":
            import json

            return json.dumps(logs, indent=2, ensure_ascii=False)
        elif format.lower() == "txt":
            return self._export_txt(logs)
        else:
            raise ValueError(f"Formato não suportado: {format}")

    def _export_txt(self, logs: List[Dict[str, Any]]) -> str:
        """Exporta logs em formato texto"""
        if not logs:
            return "Nenhum log disponível\n"

        lines = []
        for log in logs:
            timestamp = log["timestamp"]
            nivel = log["nivel"].upper()
            origem = log["origem"]
            mensagem = log["mensagem"]

            lines.append(f"[{timestamp}] {nivel} [{origem}] {mensagem}\n")

        return "".join(lines)

    def start_monitoring(self):
        """Inicia o monitoramento de logs"""
        self.is_running = True
        print("📊 Monitoramento de logs iniciado")

    def stop_monitoring(self):
        """Para o monitoramento de logs"""
        self.is_running = False
        print("⏹️ Monitoramento de logs parado")

    def set_auto_scroll(self, enabled: bool):
        """Define se o auto-scroll está habilitado"""
        self.auto_scroll = enabled
        print(f"🔄 Auto-scroll {'habilitado' if enabled else 'desabilitado'}")

    def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """Retorna os logs mais recentes"""
        with self.lock:
            return self.logs_buffer[-count:] if self.logs_buffer else []

    def get_error_logs(self) -> List[Dict[str, Any]]:
        """Retorna apenas logs de erro"""
        return self.get_logs_by_level("ERROR")

    def get_warning_logs(self) -> List[Dict[str, Any]]:
        """Retorna apenas logs de aviso"""
        return self.get_logs_by_level("WARNING")

    def get_info_logs(self) -> List[Dict[str, Any]]:
        """Retorna apenas logs de informação"""
        return self.get_logs_by_level("INFO")
