#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# ============= CONFIG GERAL =============

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Pastas alvo DEFINITIVAS
TREE = [
    SRC / "app",
    SRC / "affiliate",
    SRC / "scrapers" / "lojas",
    SRC / "scrapers" / "comunidades",
    SRC / "posting",
    SRC / "telegram_bot",
    SRC / "core",
    SRC / "utils",
    SRC / "db",
    ROOT / "apps" / "flet_dashboard",
    ROOT / "tests",
    ROOT / "scripts",
    ROOT / "docs",
]

# Mapear arquivos soltos (raiz do repo) -> destino final
# Ajuste a lista abaixo conforme sua base; coloquei os que aparecem nas capturas enviadas.
MOVE_MAP_FILES: Dict[str, Path] = {
    # scrapers de lojas (raiz -> src/scrapers/lojas)
    "aliexpress_scraper.py": SRC / "scrapers" / "lojas" / "aliexpress.py",
    "amazon_scraper.py": SRC / "scrapers" / "lojas" / "amazon.py",
    "americanas_scraper.py": SRC / "scrapers" / "lojas" / "americanas.py",
    "casas_bahia_scraper.py": SRC / "scrapers" / "lojas" / "casas_bahia.py",
    "fast_shop_scraper.py": SRC / "scrapers" / "lojas" / "fastshop.py",
    "kabum_scraper.py": SRC / "scrapers" / "lojas" / "kabum.py",
    "magalu_scraper.py": SRC / "scrapers" / "lojas" / "magalu.py",
    "submarino_scraper.py": SRC / "scrapers" / "lojas" / "submarino.py",
    "ricardo_eletro_scraper.py": SRC / "scrapers" / "lojas" / "ricardo_eletro.py",
    "shopee_scraper.py": SRC / "scrapers" / "lojas" / "shopee.py",

    # scrapers de comunidades
    "meupc_scraper.py": SRC / "scrapers" / "comunidades" / "meupcnet.py",
    "promobit_scraper.py": SRC / "scrapers" / "comunidades" / "promobit.py",
    "pelando_scraper.py": SRC / "scrapers" / "comunidades" / "pelando.py",

    # providers (viram affiliate)
    "aliexpress_api.py": SRC / "affiliate" / "aliexpress.py",
    "mercadolivre_api.py": SRC / "affiliate" / "mercadolivre.py",
    "shopee_api.py": SRC / "affiliate" / "shopee.py",

    # telegram
    "telegram/bot.py": SRC / "telegram_bot" / "bot.py",
    "telegram/__init__.py": SRC / "telegram_bot" / "__init__.py",

    # DB solto
    "garimpeiro_geek.db": SRC / "db" / "garimpeiro_geek.db",
}

# Mapeamento de substituição de imports (aplicado em TODOS .py do projeto)
# Regras conservadoras, só mexem em imports e from-imports.
IMPORT_REWRITES: Dict[str, str] = {
    # providers -> affiliate
    r"(?m)^(from\s+)providers(\s+import\s+)": r"\1affiliate\2",
    r"(?m)^(import\s+)providers(\b)": r"\1affiliate\2",
    r"(?m)^(from\s+)providers\.([a-zA-Z0-9_]+)\s+import\s+": r"\1affiliate.\2 import ",

    # telegram -> telegram_bot
    r"(?m)^(from\s+)telegram(\s+import\s+)": r"\1telegram_bot\2",
    r"(?m)^(import\s+)telegram(\b)": r"\1telegram_bot\2",
    r"(?m)^(from\s+)telegram\.bot\s+import\s+": r"\1telegram_bot.bot import ",

    # scrapers renomeados (ex.: *_scraper -> nome simples)
    r"(?m)^(from\s+)aliexpress_scraper(\s+import\s+)": r"\1scrapers.lojas.aliexpress\2",
    r"(?m)^(from\s+)amazon_scraper(\s+import\s+)": r"\1scrapers.lojas.amazon\2",
    r"(?m)^(from\s+)kabum_scraper(\s+import\s+)": r"\1scrapers.lojas.kabum\2",
    r"(?m)^(from\s+)magalu_scraper(\s+import\s+)": r"\1scrapers.lojas.magalu\2",
    r"(?m)^(from\s+)submarino_scraper(\s+import\s+)": r"\1scrapers.lojas.submarino\2",
    r"(?m)^(from\s+)casas_bahia_scraper(\s+import\s+)": r"\1scrapers.lojas.casas_bahia\2",
    r"(?m)^(from\s+)fast_shop_scraper(\s+import\s+)": r"\1scrapers.lojas.fastshop\2",
    r"(?m)^(from\s+)meupc_scraper(\s+import\s+)": r"\1scrapers.comunidades.meupcnet\2",
    r"(?m)^(from\s+)promobit_scraper(\s+import\s+)": r"\1scrapers.comunidades.promobit\2",
    r"(?m)^(from\s+)shopee_scraper(\s+import\s+)": r"\1scrapers.lojas.shopee\2",

    # imports absolutos a partir de src quando houver referencia direta de módulo
    r"(?m)^(from\s+)scrapers(\s+import\s+)": r"\1scrapers\2",
    r"(?m)^(from\s+)providers(\s+import\s+)": r"\1affiliate\2",
}

# Sufixos de backup quando houver conflito de conteúdo
BACKUP_SUFFIX = ".old.py"

# ======== util ========

def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_tree(paths: Iterable[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def find_candidates() -> List[Path]:
    """Arquivos na raiz (e subpastas imediatas) que queremos avaliar para mover."""
    cands: List[Path] = []
    for name in MOVE_MAP_FILES.keys():
        p = ROOT / name
        if p.exists():
            cands.append(p)
    return cands

@dataclass
class MoveAction:
    src: Path
    dst: Path
    action: str  # "move", "skip-dup", "backup+move"

def plan_moves() -> List[MoveAction]:
    actions: List[MoveAction] = []
    for rel, dst in MOVE_MAP_FILES.items():
        src = ROOT / rel
        if not src.exists():
            continue
        if dst.exists():
            if sha256_of(src) == sha256_of(dst):
                actions.append(MoveAction(src, dst, "skip-dup"))
            else:
                actions.append(MoveAction(src, dst, "backup+move"))
        else:
            actions.append(MoveAction(src, dst, "move"))
    return actions

def do_moves(actions: List[MoveAction], apply: bool) -> None:
    for a in actions:
        a.dst.parent.mkdir(parents=True, exist_ok=True)
        if a.action == "skip-dup":
            print(f"[skip-dup] {a.src} == {a.dst}")
            if apply:
                try:
                    a.src.unlink()
                except Exception:
                    pass
            continue
        if a.action == "backup+move":
            bak = a.dst.with_suffix(a.dst.suffix + BACKUP_SUFFIX)
            print(f"[backup] {a.dst} -> {bak}")
            print(f"[move]   {a.src} -> {a.dst}")
            if apply:
                shutil.move(str(a.dst), str(bak))
                shutil.move(str(a.src), str(a.dst))
            continue
        if a.action == "move":
            print(f"[move]   {a.src} -> {a.dst}")
            if apply:
                shutil.move(str(a.src), str(a.dst))

# ======== reescrita de imports ========

IMPORT_LINE_RE = re.compile(r"^(from\s+[.\w]+\s+import\s+.+|import\s+[.\w]+)", re.MULTILINE)

def rewrite_imports_in_file(p: Path, rewrites: Dict[str, str]) -> Tuple[bool, str]:
    """Reescreve imports segundo as regras. Retorna (alterou?, preview)."""
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return False, ""
    original = text
    for pat, rep in rewrites.items():
        text = re.sub(pat, rep, text)
    if text != original:
        return True, text
    return False, ""

def apply_import_rewrites(apply: bool) -> List[Path]:
    changed: List[Path] = []
    for py in ROOT.rglob("*.py"):
        # não reescrever arquivos de .venv, .git, etc.
        if any(part in {".venv", ".git", ".playwright", ".chromium", "__pycache__"} for part in py.parts):
            continue
        # não mexer neste script
        if py == Path(__file__).resolve():
            continue
        changed_flag, new_text = rewrite_imports_in_file(py, IMPORT_REWRITES)
        if changed_flag:
            changed.append(py)
            print(f"[imports] rewrite {py}")
            if apply:
                py.write_text(new_text, encoding="utf-8")
    return changed

# ======== main ========

def main() -> None:
    parser = argparse.ArgumentParser(description="Reorganiza o projeto para a estrutura padrão.")
    parser.add_argument("--apply", action="store_true", help="Aplica as mudanças (sem este flag é dry-run).")
    args = parser.parse_args()

    print(f"ROOT = {ROOT}")
    ensure_tree(TREE)

    # 1) Planejar e mover
    actions = plan_moves()
    if not actions:
        print("Nenhum arquivo mapeado para mover (ok).")
    else:
        print("\nPlano de movimentação:")
        for a in actions:
            print(f" - {a.action:11s} {a.src.relative_to(ROOT)}  ->  {a.dst.relative_to(ROOT)}")

    if args.apply:
        print("\n==> Executando movimentos...")
        do_moves(actions, apply=True)
    else:
        print("\n(DRY-RUN) Nada foi movido. Rode com --apply para aplicar.")

    # 2) Reescrever imports
    print("\nReescrevendo imports conforme regras...")
    changed_files = apply_import_rewrites(apply=args.apply)
    if not changed_files:
        print("Nenhum import precisou ser reescrito (ok).")
    else:
        print(f"Total de arquivos com imports atualizados: {len(changed_files)}")

    # 3) Lembretes finais
    print("\n=== PRÓXIMOS PASSOS ===")
    print("1) Verifique diffs e rode: make fmt && make lint && make type && make test")
    print("2) Ajuste manualmente qualquer import específico que não tenha regra aqui.")
    print("3) Confirme se o bot roda em modo sandbox antes de publicar em canal oficial.")

if __name__ == "__main__":
    sys.exit(main())
