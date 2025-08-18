# services/control_service.py
import threading
import time
import logging
from typing import Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    STOPPED = "parado"
    RUNNING = "rodando"
    ERROR = "erro"
    STARTING = "iniciando"
    STOPPING = "parando"


class ControlService:
    def __init__(self):
        self.status = SystemStatus.STOPPED
        self.status_lock = threading.Lock()
        self.control_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.status_callbacks: list[Callable[[SystemStatus], None]] = []

        # Contadores para simulação
        self.ofertas_encontradas = 0
        self.ofertas_postadas = 0
        self.erros = 0

    def add_status_callback(self, callback: Callable[[SystemStatus], None]):
        """Adiciona callback para mudanças de status"""
        self.status_callbacks.append(callback)

    def _notify_status_change(self, new_status: SystemStatus):
        """Notifica mudanças de status"""
        with self.status_lock:
            self.status = new_status

        # Notifica callbacks em thread separada
        for callback in self.status_callbacks:
            try:
                callback(new_status)
            except Exception as e:
                logger.error(f"Erro no callback de status: {e}")

    def get_status(self) -> SystemStatus:
        """Retorna status atual"""
        with self.status_lock:
            return self.status

    def start_system(self) -> bool:
        """Inicia o sistema"""
        if self.status in [SystemStatus.RUNNING, SystemStatus.STARTING]:
            logger.warning("Sistema já está rodando ou iniciando")
            return False

        try:
            self._notify_status_change(SystemStatus.STARTING)
            self.stop_flag.clear()

            # Inicia thread de controle
            self.control_thread = threading.Thread(target=self._run_system, daemon=True)
            self.control_thread.start()

            logger.info("Sistema iniciado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar sistema: {e}")
            self._notify_status_change(SystemStatus.ERROR)
            return False

    def stop_system(self) -> bool:
        """Para o sistema"""
        if self.status in [SystemStatus.STOPPED, SystemStatus.STOPPING]:
            logger.warning("Sistema já está parado ou parando")
            return False

        try:
            self._notify_status_change(SystemStatus.STOPPING)
            self.stop_flag.set()

            # Aguarda thread parar
            if self.control_thread and self.control_thread.is_alive():
                self.control_thread.join(timeout=5.0)

            self._notify_status_change(SystemStatus.STOPPED)
            logger.info("Sistema parado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao parar sistema: {e}")
            self._notify_status_change(SystemStatus.ERROR)
            return False

    def _run_system(self):
        """Loop principal do sistema (simulado)"""
        try:
            self._notify_status_change(SystemStatus.RUNNING)

            while not self.stop_flag.is_set():
                # Simula trabalho do sistema
                time.sleep(2)

                # Simula encontro de ofertas
                if not self.stop_flag.is_set():
                    self.ofertas_encontradas += 1
                    logger.info(f"Oferta encontrada #{self.ofertas_encontradas}")

                # Simula postagem
                if not self.stop_flag.is_set() and self.ofertas_encontradas % 3 == 0:
                    self.ofertas_postadas += 1
                    logger.info(f"Oferta postada #{self.ofertas_postadas}")

                # Simula erro ocasional
                if not self.stop_flag.is_set() and self.ofertas_encontradas % 10 == 0:
                    self.erros += 1
                    logger.warning(f"Erro simulado #{self.erros}")

        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            self._notify_status_change(SystemStatus.ERROR)

    def get_stats(self) -> dict:
        """Retorna estatísticas do sistema"""
        return {
            "ofertas_encontradas": self.ofertas_encontradas,
            "ofertas_postadas": self.ofertas_postadas,
            "erros": self.erros,
            "status": self.status.value,
        }

    def reset_stats(self):
        """Reseta estatísticas"""
        self.ofertas_encontradas = 0
        self.ofertas_postadas = 0
        self.erros = 0

    def force_collection(self) -> bool:
        """Força uma coleta imediata"""
        if self.status != SystemStatus.RUNNING:
            logger.warning("Sistema deve estar rodando para forçar coleta")
            return False

        try:
            logger.info("Coleta forçada iniciada")
            # Simula coleta forçada
            time.sleep(1)
            self.ofertas_encontradas += 5
            logger.info("Coleta forçada concluída")
            return True
        except Exception as e:
            logger.error(f"Erro na coleta forçada: {e}")
            return False

    def check_health(self) -> dict:
        """Verifica saúde do sistema"""
        health = {
            "status": self.status.value,
            "thread_alive": self.control_thread.is_alive()
            if self.control_thread
            else False,
            "uptime": time.time() if self.status == SystemStatus.RUNNING else 0,
            "stats": self.get_stats(),
        }

        # Determina se está saudável
        if self.status == SystemStatus.RUNNING and health["thread_alive"]:
            health["healthy"] = True
            health["message"] = "Sistema funcionando normalmente"
        elif self.status == SystemStatus.STOPPED:
            health["healthy"] = True
            health["message"] = "Sistema parado (normal)"
        else:
            health["healthy"] = False
            health["message"] = "Sistema com problemas"

        return health


# Instância global
control_service = ControlService()
