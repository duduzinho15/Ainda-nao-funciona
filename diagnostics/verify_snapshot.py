# diagnostics/verify_snapshot.py
from __future__ import annotations
import sys, difflib, pathlib

BASELINE = pathlib.Path("tests/baselines/ui_snapshot.txt")
CURRENT  = pathlib.Path("ui_snapshot.txt")

def main():
    if not BASELINE.exists() or not CURRENT.exists():
        print("Arquivos de snapshot ausentes.")
        print(f"Baseline: {BASELINE.absolute()}")
        print(f"Current: {CURRENT.absolute()}")
        sys.exit(3)
        
    a = BASELINE.read_text(encoding="utf-8").splitlines(keepends=True)
    b = CURRENT.read_text(encoding="utf-8").splitlines(keepends=True)
    
    if a == b:
        print("✅ Snapshot OK (sem diffs).")
        return 0
        
    print("⚠️ Snapshot mudou! Diff:\n")
    for line in difflib.unified_diff(a, b, fromfile="baseline", tofile="current"):
        sys.stdout.write(line)
    print(f"\n💡 Para atualizar o baseline:")
    print(f"   copy ui_snapshot.txt tests\\baselines\\ui_snapshot.txt")
    return 4

if __name__ == "__main__":
    sys.exit(main())

