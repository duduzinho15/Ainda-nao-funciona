"""
CSV export system for offers
"""
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List
from .models import Oferta

class CSVExporter:
    """Sistema de exportação CSV para ofertas"""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = Path(export_dir)
        self._ensure_export_dir()
    
    def _ensure_export_dir(self):
        """Garante que o diretório de exportação existe"""
        self.export_dir.mkdir(exist_ok=True)
    
    def export_ofertas(self, ofertas: List[Oferta], filename: str = None) -> str:
        """Exporta ofertas para CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"ofertas_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Título', 'Loja', 'Preço', 'Preço Original', 
                    'URL', 'Imagem', 'Data Criação', 'Fonte'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for oferta in ofertas:
                    writer.writerow({
                        'Título': oferta.titulo,
                        'Loja': oferta.loja,
                        'Preço': oferta.preco_formatado() if oferta.preco else 'N/A',
                        'Preço Original': oferta.preco_original_formatado() if oferta.preco_original else 'N/A',
                        'URL': oferta.url,
                        'Imagem': oferta.imagem_url or 'N/A',
                        'Data Criação': oferta.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        'Fonte': oferta.fonte
                    })
            
            return str(filepath)
        
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            raise
    
    def export_deterministic_csv(self, periodo: str = "all") -> str:
        """Exporta CSV determinístico para CI"""
        from .data_service import DataService
        
        # Gerar dados determinísticos
        data_service = DataService()
        ofertas = data_service._get_deterministic_ofertas(periodo)
        
        # Nome de arquivo determinístico
        filename = f"ofertas_ci_{periodo}.csv"
        
        return self.export_ofertas(ofertas, filename)
    
    def get_export_path(self) -> str:
        """Retorna o caminho do diretório de exportação"""
        return str(self.export_dir.absolute())
    
    def list_exports(self) -> List[str]:
        """Lista todos os arquivos CSV exportados"""
        csv_files = list(self.export_dir.glob("*.csv"))
        return [f.name for f in sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True)]
    
    def cleanup_old_exports(self, keep_days: int = 30):
        """Remove exportações antigas"""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
        
        for csv_file in self.export_dir.glob("*.csv"):
            if csv_file.stat().st_mtime < cutoff_time:
                try:
                    csv_file.unlink()
                    print(f"Arquivo antigo removido: {csv_file.name}")
                except Exception as e:
                    print(f"Erro ao remover arquivo antigo {csv_file.name}: {e}")

# Instância global
csv_exporter = CSVExporter()

