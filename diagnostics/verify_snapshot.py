# diagnostics/verify_snapshot.py
from __future__ import annotations
import sys, difflib, pathlib, re

BASELINE = pathlib.Path("tests/baselines/ui_snapshot.txt")
CURRENT  = pathlib.Path("ui_snapshot.txt")

def normalize_snapshot(txt: str) -> str:
    """Normaliza snapshot para evitar diffs desnecessários"""
    # Horas: 12:34:56 -> <TIME>
    txt = re.sub(r"\b\d{1,2}:\d{2}:\d{2}\b", "<TIME>", txt)
    # Datas ISO: 2025-08-18 -> <DATE>
    txt = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "<DATE>", txt)
    # Preços: R$ 1.234,56 -> R$ <VAL>
    txt = re.sub(r"R\$\s*\d[\d\.\,]*", "R$ <VAL>", txt)
    # IDs/hash/uuid comuns
    txt = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", "<UUID>", txt, flags=re.I)
    
    # Normalizações para CSV e arquivos
    # Timestamps de CSV: 2025-08-18 20:30:45 -> <CSV_TIMESTAMP>
    txt = re.sub(r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b", "<CSV_TIMESTAMP>", txt)
    # Nomes de arquivo CSV: ofertas_2025-08-18_20-30-45.csv -> <CSV_FILENAME>
    txt = re.sub(r"ofertas_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv", "<CSV_FILENAME>", txt)
    # Caminhos de exportação: ./exports/ofertas_*.csv -> <EXPORT_PATH>
    txt = re.sub(r"\./exports/ofertas_[^\.]+\.csv", "<EXPORT_PATH>", txt)
    
    return txt

def main():
    if not BASELINE.exists() or not CURRENT.exists():
        print("Arquivos de snapshot ausentes.")
        print(f"Baseline: {BASELINE.absolute()}")
        print(f"Current: {CURRENT.absolute()}")
        sys.exit(3)

    # Normalizar ambos os snapshots
    cur = normalize_snapshot(CURRENT.read_text(encoding="utf-8"))
    base = normalize_snapshot(BASELINE.read_text(encoding="utf-8"))

    if cur == base:
        print("✅ Snapshot OK (sem diffs após normalização).")
        return 0

    # Gerar diff detalhado
    print("⚠️ Snapshot mudou! Diff (após normalização):\n")
    diff = difflib.unified_diff(base.splitlines(), cur.splitlines(), fromfile="baseline", tofile="current")
    for line in diff:
        sys.stdout.write(line)
    
    # Salvar diff em arquivo para análise
    diff_content = "\n".join(difflib.unified_diff(base.splitlines(), cur.splitlines(), fromfile="baseline", tofile="current"))
    pathlib.Path("ui_snapshot.diff").write_text(diff_content, encoding="utf-8")
    
    print(f"\n💡 Para atualizar o baseline:")
    print(f"   copy ui_snapshot.txt tests\\baselines\\ui_snapshot.txt")
    print(f"\n📁 Diff salvo em: ui_snapshot.diff")
    return 4

if __name__ == "__main__":
    sys.exit(main())

