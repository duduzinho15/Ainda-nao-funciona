"""
Live logs system for dashboard
"""
import asyncio
import os
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime

class LiveLogReader:
    """Sistema de leitura de logs ao vivo"""
    
    def __init__(self, log_file: str = ".data/logs/app.log", max_lines: int = 500):
        self.log_file = Path(log_file)
        self.max_lines = max_lines
        self._last_position = 0
        self._lines_buffer = []
        self._callbacks = []
        self._running = False
        self._task = None
    
    def add_callback(self, callback: Callable[[List[str]], None]):
        """Adiciona callback para receber atualizações de logs"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[List[str]], None]):
        """Remove callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def start_monitoring(self):
        """Inicia monitoramento de logs"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Para monitoramento de logs"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self._running:
            try:
                await self._check_for_updates()
                await asyncio.sleep(0.5)  # Verificar a cada 500ms
            except Exception as e:
                print(f"Erro no monitoramento de logs: {e}")
                await asyncio.sleep(1)
    
    async def _check_for_updates(self):
        """Verifica se há atualizações no arquivo de log"""
        if not self.log_file.exists():
            # Arquivo não existe, notificar callbacks
            await self._notify_callbacks(["Aguardando logs..."])
            return
        
        try:
            current_size = self.log_file.stat().st_size
            
            if current_size < self._last_position:
                # Arquivo foi truncado (limpo)
                self._last_position = 0
                self._lines_buffer = []
            
            if current_size > self._last_position:
                # Há novos dados
                await self._read_new_lines()
                self._last_position = current_size
                
        except Exception as e:
            print(f"Erro ao verificar logs: {e}")
    
    async def _read_new_lines(self):
        """Lê novas linhas do arquivo de log"""
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self._last_position)
                new_lines = f.readlines()
                
                if new_lines:
                    # Adicionar novas linhas ao buffer
                    self._lines_buffer.extend(new_lines)
                    
                    # Manter apenas as últimas max_lines
                    if len(self._lines_buffer) > self.max_lines:
                        self._lines_buffer = self._lines_buffer[-self.max_lines:]
                    
                    # Notificar callbacks
                    await self._notify_callbacks(self._lines_buffer)
                    
        except Exception as e:
            print(f"Erro ao ler logs: {e}")
    
    async def _notify_callbacks(self, lines: List[str]):
        """Notifica todos os callbacks registrados"""
        if not self._callbacks:
            return
        
        # Filtrar linhas por nível se necessário
        filtered_lines = self._filter_lines(lines)
        
        for callback in self._callbacks:
            try:
                # Executar callback de forma assíncrona
                if asyncio.iscoroutinefunction(callback):
                    await callback(filtered_lines)
                else:
                    # Se não for async, executar em thread separada
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, callback, filtered_lines)
            except Exception as e:
                print(f"Erro em callback de logs: {e}")
    
    def _filter_lines(self, lines: List[str]) -> List[str]:
        """Filtra linhas por nível de log"""
        filtered = []
        for line in lines:
            line_lower = line.lower()
            if any(level in line_lower for level in ["error", "warn", "info", "debug"]):
                filtered.append(line)
            else:
                # Incluir linhas que não têm nível explícito
                filtered.append(line)
        return filtered
    
    def get_current_logs(self) -> List[str]:
        """Retorna logs atuais (para inicialização)"""
        if not self.log_file.exists():
            return ["Aguardando logs..."]
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Retornar apenas as últimas max_lines
                return lines[-self.max_lines:] if len(lines) > self.max_lines else lines
        except Exception as e:
            print(f"Erro ao ler logs atuais: {e}")
            return ["Erro ao carregar logs..."]
    
    def clear_buffer(self):
        """Limpa buffer de logs"""
        self._lines_buffer = []
        self._last_position = 0

# Instância global
live_log_reader = LiveLogReader()

