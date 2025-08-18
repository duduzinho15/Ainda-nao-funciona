# diagnostics/ui_reporter.py
from __future__ import annotations
from collections import Counter
from typing import Iterable, List, Dict, Any
import sys, json, io

try:
    # opcional: visual colorido no terminal
    from rich import print as rprint  # type: ignore
    from rich.tree import Tree  # type: ignore
    from rich.panel import Panel  # type: ignore
    from rich.table import Table  # type: ignore
    HAVE_RICH = True
except Exception:
    HAVE_RICH = False

def _children(ctrl) -> Iterable:
    slots = ("controls", "content", "leading", "trailing", "title", "subtitle",
             "prefix", "suffix", "tabs")
    for name in slots:
        val = getattr(ctrl, name, None)
        if not val:
            continue
        if isinstance(val, list):
            for c in val:
                if getattr(c, "__class__", None) is not None:
                    yield c
        else:
            yield val

def _flatten(root) -> List:
    out, stack = [], [root]
    seen = set()
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        out.append(node)
        for ch in reversed(list(_children(node))):
            stack.append(ch)
    return out

def _index_by_key(nodes: List) -> Dict[str, Any]:
    idx = {}
    for n in nodes:
        k = getattr(n, "key", None)
        if k:
            idx[str(k)] = n
    return idx

def _safe(name: str, obj, default=""):
    try:
        return getattr(obj, name, default)
    except Exception:
        return default

def _chip_state_text(chip) -> str:
    bg = str(_safe("bgcolor", chip, ""))
    text = str(_safe("text", chip, ""))
    sel = "OK " if ("BLUE" in bg or "seed" in bg or "Primary" in bg) else ""
    return f"[{sel}{text}]"

def _acceptance_checks(idx: Dict[str, Any], nodes: List) -> Dict[str, bool]:
    checks = {
        "tem_tabs": ("tabs" in idx) or any(n.__class__.__name__ == "Tabs" for n in nodes),
        "tem_quatro_cards": sum("card_" in k for k in idx.keys()) >= 4,
        "tem_filtros_periodo": "filters" in idx,
        "tem_toggle_tema": any(n.__class__.__name__ == "IconButton" for n in nodes),
        "tem_painel_grafico": "chart" in idx,
        "tem_painel_logs": "logs" in idx,
    }
    
    # Checks extras para conteúdo específico
    # Card de preço médio mostra "R$"
    preco_card = idx.get("card_preco")
    if preco_card:
        text_nodes = [n for n in _flatten(preco_card) if n.__class__.__name__ == "Text"]
        checks["preco_tem_prefixo_moeda"] = any("R$" in str(getattr(t, "value", "") or "") for t in text_nodes)
    
    # Card de ofertas mostra número
    ofertas_card = idx.get("card_ofertas")
    if ofertas_card:
        text_nodes = [n for n in _flatten(ofertas_card) if n.__class__.__name__ == "Text"]
        checks["ofertas_tem_numero"] = any(str(getattr(t, "value", "") or "").isdigit() for t in text_nodes)
    
    # Card de lojas mostra número
    lojas_card = idx.get("card_lojas")
    if lojas_card:
        text_nodes = [n for n in _flatten(lojas_card) if n.__class__.__name__ == "Text"]
        checks["lojas_tem_numero"] = any(str(getattr(t, "value", "") or "").isdigit() for t in text_nodes)
    
    # Gráfico tem conteúdo mínimo
    chart = idx.get("chart")
    if chart:
        # Verificar se há texto no gráfico (indicando conteúdo)
        chart_texts = [n for n in _flatten(chart) if n.__class__.__name__ == "Text"]
        checks["grafico_tem_conteudo"] = len(chart_texts) >= 2  # título + placeholder
    
    return checks

def _ascii_snapshot(page, nodes: List, idx: Dict[str, Any]) -> str:
    buf = io.StringIO()
    title = "Garimpeiro Geek - Dashboard"
    theme = getattr(page, "theme_mode", None)
    tname = "Dark" if str(theme).endswith("DARK") else "Light"
    print(f"+ {title}  (Tema: {tname})", file=buf)

    tabs = None
    for n in nodes:
        if n.__class__.__name__ == "Tabs":
            tabs = n; break
    if tabs:
        items = []
        for i, t in enumerate(getattr(tabs, "tabs", []) or []):
            txt = _safe("text", t, f"Tab {i+1}")
            sel = getattr(tabs, "selected_index", 0) == i
            items.append(f"[{'*' if sel else ' '}] {txt}")
        print("+ Tabs: " + " | ".join(items), file=buf)

    cards = [idx.get(k) for k in sorted(idx) if k.startswith("card_")]
    if cards:
        print("+ Cards:", file=buf)
        for c in cards:
            if not c:
                continue
            label = ""; value = ""
            for child in _flatten(c):
                if child.__class__.__name__ == "Text":
                    txt = str(_safe("value", child, "") or _safe("data", child, ""))
                    if not label:
                        label = txt
                    else:
                        value = txt
            print(f"|  * {label} -> {value}", file=buf)

    filters = idx.get("filters")
    if filters:
        chips = []
        for n in _flatten(filters):
            if n.__class__.__name__ in ("CupertinoButton","TextButton"):
                chips.append(_chip_state_text(n))
        if chips:
            print("+ Filtros: " + "  ".join(chips), file=buf)

    if "chart" in idx:
        print("+ Grafico: Distribuicao por Loja (painel encontrado)", file=buf)
    if "logs" in idx:
        print("+ Logs: painel encontrado", file=buf)
    return buf.getvalue()

def emit_junit_xml(summary: dict, path: str) -> None:
    """Exporta resultados como JUnit XML para integração com CI"""
    import xml.etree.ElementTree as ET
    from datetime import datetime

    checks = summary.get("checks", {})
    ts = ET.Element(
        "testsuite",
        {
            "name": "UIReporter",
            "tests": str(len(checks)),
            "failures": str(sum(0 if v else 1 for v in checks.values())),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )
    for name, ok in checks.items():
        tc = ET.SubElement(ts, "testcase", {"classname": "UI", "name": name})
        if not ok:
            fail = ET.SubElement(tc, "failure", {"message": f"check '{name}' failed"})
            fail.text = summary.get("snapshot", "")[:50000]  # snapshot parcial ajuda no debug
    ET.ElementTree(ts).write(path, encoding="utf-8", xml_declaration=True)

def dump_report(page, *, json_summary: bool = False, filepath: str | None = "ui_snapshot.txt") -> Dict[str, Any]:
    nodes = []
    for root in getattr(page, "controls", []):
        nodes.extend(_flatten(root))
    idx = _index_by_key(nodes)
    types = Counter(n.__class__.__name__ for n in nodes)

    try:
        import flet as ft  # type: ignore
        flet_ver = getattr(ft, "__version__", "unknown")
    except Exception:
        flet_ver = "unknown"

    checks = _acceptance_checks(idx, nodes)
    ascii_view = _ascii_snapshot(page, nodes, idx)

    # Para JSON, não usar rich para evitar problemas de encoding
    if HAVE_RICH and not json_summary:
        tree = Tree(f"[b]Árvore de Controles[/b]  (tot: {len(nodes)})")
        def add(node, parent):
            label = f"{node.__class__.__name__}  key={getattr(node,'key',None)}"
            sub = parent.add(label)
            for ch in _children(node):
                add(ch, sub)
        r = Tree("root")
        for root in getattr(page, "controls", []):
            add(root, r)
        stats = Table(title="Resumo técnico")
        stats.add_column("Item"); stats.add_column("Valor")
        stats.add_row("Flet", flet_ver)
        stats.add_row("Controles únicos", str(len(types)))
        stats.add_row("Top tipos", ", ".join(f"{k}({v})" for k,v in types.most_common(6)))

        rprint(Panel.fit(stats, title="Garimpeiro Geek – UI Reporter"))
        rprint(Panel.fit(ascii_view, title="Snapshot visual (ASCII)"))
        rprint(Panel(r, title="Árvore de controles"))

        chk = Table(title="Checks de aceite")
        chk.add_column("Check"); chk.add_column("OK?")
        for k, v in checks.items():
            chk.add_row(k, "✅" if v else "❌")
        rprint(Panel.fit(chk, title="Validações"))
    else:
        print("\n=== UI REPORT ===")
        print(f"Flet: {flet_ver}")
        print(f"Tipos de controle: {dict(types.most_common(6))}")
        print("\n--- Snapshot visual ---")
        print(ascii_view)
        print("--- Checks ---")
        for k, v in checks.items():
            print(f"{k}: {'OK' if v else 'FALHOU'}")

    if filepath:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(ascii_view + "\n\n")
                f.write("CHECKS:\n")
                for k, v in checks.items():
                    f.write(f"- {k}: {'OK' if v else 'FALHOU'}\n")
        except Exception:
            pass

    summary = {
        "flet_version": flet_ver,
        "control_types": dict(types),
        "checks": checks,
        "has_rich": HAVE_RICH,
        "snapshot": ascii_view,
        "output_file": filepath,
    }
    if json_summary:
        # Para JSON, usar apenas texto simples sem rich
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary
