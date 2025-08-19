"""
Sistema de exportação CSV para o dashboard.
Exporta ofertas para arquivos CSV com feedback visual.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .models import Oferta


class CSVExporter:
    """Exportador de ofertas para CSV."""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_ofertas(self, ofertas: List[Oferta], periodo: str = "all", 
                       filename: Optional[str] = None) -> Dict[str, any]:
        """
        Exporta ofertas para arquivo CSV.
        
        Args:
            ofertas: Lista de ofertas para exportar
            periodo: Período dos dados (24h, 7d, 30d, all)
            filename: Nome personalizado do arquivo (opcional)
            
        Returns:
            Dicionário com informações da exportação
        """
        try:
            # Gerar nome do arquivo
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ofertas_{periodo}_{timestamp}.csv"
            
            # Verificar se estamos em modo CI (determinístico)
            is_ci = os.getenv("GG_SEED") and os.getenv("GG_FREEZE_TIME")
            if is_ci:
                filename = f"ofertas_ci_{periodo}.csv"
            
            filepath = self.export_dir / filename
            
            # Converter ofertas para formato CSV
            csv_data = self._prepare_csv_data(ofertas)
            
            # Escrever arquivo CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
            
            # Estatísticas da exportação
            stats = {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'total_ofertas': len(ofertas),
                'periodo': periodo,
                'is_ci': is_ci,
                'timestamp': datetime.now().isoformat(),
                'file_size': filepath.stat().st_size
            }
            
            print(f"✅ CSV exportado com sucesso: {filename}")
            print(f"   📁 Local: {filepath}")
            print(f"   📊 Ofertas: {len(ofertas)}")
            print(f"   📏 Tamanho: {stats['file_size']} bytes")
            
            return stats
            
        except Exception as e:
            error_info = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"❌ Erro ao exportar CSV: {e}")
            return error_info
    
    def _prepare_csv_data(self, ofertas: List[Oferta]) -> List[Dict[str, any]]:
        """
        Prepara dados das ofertas para formato CSV.
        
        Args:
            ofertas: Lista de ofertas
            
        Returns:
            Lista de dicionários com dados formatados para CSV
        """
        csv_data = []
        
        for oferta in ofertas:
            # Formatar preços
            preco_str = f"R$ {oferta.preco:.2f}" if oferta.preco else "N/A"
            preco_original_str = f"R$ {oferta.preco_original:.2f}" if oferta.preco_original else "N/A"
            
            # Formatar data
            data_str = oferta.created_at.strftime("%Y-%m-%d %H:%M:%S") if oferta.created_at else "N/A"
            
            # Calcular desconto
            desconto = 0
            if oferta.preco and oferta.preco_original:
                desconto = ((oferta.preco_original - oferta.preco) / oferta.preco_original) * 100
            
            desconto_str = f"{desconto:.1f}%" if desconto > 0 else "0%"
            
            row = {
                'titulo': oferta.titulo or 'N/A',
                'loja': oferta.loja or 'N/A',
                'preco_atual': preco_str,
                'preco_original': preco_original_str,
                'desconto': desconto_str,
                'url': oferta.url or 'N/A',
                'imagem_url': oferta.imagem_url or 'N/A',
                'data_criacao': data_str,
                'fonte': oferta.fonte or 'N/A'
            }
            
            csv_data.append(row)
        
        return csv_data
    
    def get_export_history(self) -> List[Dict[str, any]]:
        """
        Retorna histórico de exportações.
        
        Returns:
            Lista de informações sobre arquivos exportados
        """
        history = []
        
        try:
            for filepath in self.export_dir.glob("ofertas_*.csv"):
                stats = filepath.stat()
                history.append({
                    'filename': filepath.name,
                    'filepath': str(filepath),
                    'size_bytes': stats.st_size,
                    'created_at': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    'modified_at': datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
            
            # Ordenar por data de criação (mais recente primeiro)
            history.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao ler histórico de exportações: {e}")
        
        return history
    
    def cleanup_old_exports(self, keep_days: int = 30) -> Dict[str, any]:
        """
        Remove exportações antigas para economizar espaço.
        
        Args:
            keep_days: Número de dias para manter arquivos
            
        Returns:
            Dicionário com estatísticas da limpeza
        """
        try:
            cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            removed_count = 0
            removed_size = 0
            
            for filepath in self.export_dir.glob("ofertas_*.csv"):
                if filepath.stat().st_mtime < cutoff_date:
                    file_size = filepath.stat().st_size
                    filepath.unlink()
                    removed_count += 1
                    removed_size += file_size
                    print(f"🗑️ Arquivo removido: {filepath.name}")
            
            stats = {
                'success': True,
                'removed_files': removed_count,
                'removed_size_bytes': removed_size,
                'kept_days': keep_days
            }
            
            if removed_count > 0:
                print(f"🧹 Limpeza concluída: {removed_count} arquivos removidos")
                print(f"   💾 Espaço liberado: {removed_size} bytes")
            else:
                print("✨ Nenhum arquivo antigo encontrado para remoção")
            
            return stats
            
        except Exception as e:
            error_info = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ Erro durante limpeza: {e}")
            return error_info
    
    def get_export_stats(self) -> Dict[str, any]:
        """
        Retorna estatísticas gerais das exportações.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            files = list(self.export_dir.glob("ofertas_*.csv"))
            total_files = len(files)
            total_size = sum(f.stat().st_size for f in files)
            
            # Agrupar por período
            period_stats = {}
            for filepath in files:
                filename = filepath.name
                if 'ci_' in filename:
                    period = filename.split('ci_')[1].split('.')[0]
                else:
                    period = filename.split('_')[1] if '_' in filename else 'unknown'
                
                period_stats[period] = period_stats.get(period, 0) + 1
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'period_distribution': period_stats,
                'export_dir': str(self.export_dir)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'export_dir': str(self.export_dir)
            }

