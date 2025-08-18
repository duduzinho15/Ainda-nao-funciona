# flet_app/premium_dashboard.py
from __future__ import annotations
import os, sys, argparse, sqlite3, datetime as dt, contextlib, math
import flet as ft
from .compatibility import (
    get_error_colors, get_outline_color, get_theme_icon,
    safe_theme_colors, check_compatibility
)

# Evita erros de encoding no Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DB_PATH = os.getenv("DB_PATH", "ofertas.db")

# ---------------------- DB helpers ----------------------
def open_conn():
    try:
        if not os.path.exists(DB_PATH):
            return None
        return sqlite3.connect(DB_PATH)
    except Exception:
        return None

def find_table_and_cols(conn: sqlite3.Connection):
    """
    Tenta detectar a tabela e mapear colunas padrão.
    Retorna (table, mapping_dict) ou (None, {})
    mapping: {title, store, price, created_at, url}
    """
    wanted = {"titulo","title","name"}, {"loja","store","seller"}, {"preco","price","valor"}, {"created_at","data","date","timestamp","ts"}, {"url","link","href"}
    with conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        cols = set()
        with conn:
            cur = conn.execute(f"PRAGMA table_info('{t}')")
            col_list = [r[1] for r in cur.fetchall()]
        cols = set(c.lower() for c in col_list)
        def pick(cands): 
            for c in cands:
                if c in cols: 
                    # devolve exatamente o nome como está no banco (case)
                    return next(x for x in col_list if x.lower()==c)
            return None
        title = pick(wanted[0])
        store = pick(wanted[1])
        price = pick(wanted[2])
        created = pick(wanted[3])
        url = pick(wanted[4])
        if title and store and price and created:
            return t, {"title":title, "store":store, "price":price, "created_at":created, "url": url}
    return None, {}

def q_scalar(conn, sql, params=()):
    with conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else 0

def get_metrics(conn, table, m, since: dt.datetime|None=None):
    where = ""
    params = []
    if since is not None:
        where = f"WHERE {m['created_at']} >= ?"
        params.append(since.isoformat(sep=' '))
    total = q_scalar(conn, f"SELECT COUNT(*) FROM {table} {where}", params)
    stores = q_scalar(conn, f"SELECT COUNT(DISTINCT {m['store']}) FROM {table} {where}", params)
    avg = q_scalar(conn, f"SELECT AVG(CAST({m['price']} AS FLOAT)) FROM {table} {where}", params)
    return {"total": total, "stores": stores, "avg_price": avg}

def offers_by_store(conn, table, m, since: dt.datetime|None=None, limit=8):
    where = ""
    params=[]
    if since:
        where=f"WHERE {m['created_at']} >= ?"
        params.append(since.isoformat(sep=' '))
    sql = f"""SELECT {m['store']}, COUNT(*) 
              FROM {table} {where}
              GROUP BY {m['store']}
              ORDER BY 2 DESC
              LIMIT {int(limit)}"""
    with conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    return [(r[0], r[1]) for r in rows]

def fetch_offers(conn, table, m, page:int, page_size:int, since:dt.datetime|None=None):
    off = (page-1)*page_size
    where = ""
    params=[]
    if since:
        where = f"WHERE {m['created_at']} >= ?"
        params.append(since.isoformat(sep=' '))
    sql = f"""SELECT {m['created_at']}, {m['title']}, {m['store']}, {m['price']}, {m.get('url') or "NULL"}
              FROM {table}
              {where}
              ORDER BY {m['created_at']} DESC
              LIMIT ? OFFSET ?"""
    params.extend([page_size, off])
    with conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    return rows

def count_offers(conn, table, m, since:dt.datetime|None=None):
    where = ""
    params=[]
    if since:
        where=f"WHERE {m['created_at']} >= ?"
        params.append(since.isoformat(sep=' '))
    return q_scalar(conn, f"SELECT COUNT(*) FROM {table} {where}", params)

# ---------------------- UI helpers ----------------------
def color_tokens(page: ft.Page):
    """Retorna tokens de cor com compatibilidade total."""
    colors = safe_theme_colors(page)
    error_colors = get_error_colors()
    
    return dict(
        BG=colors['background'],
        SURF=colors['surface'],
        ON_SURF=colors['on_surface'],
        PRIMARY=colors['primary'],
        ON_PRIMARY=colors['on_primary'],
        ERROR=error_colors['ERROR'],
        ON_ERROR=error_colors['ON_ERROR'],
        OUTLINE=colors['outline'],
    )

def card(page: ft.Page, child, padding=16, expand=False):
    C = color_tokens(page)
    return ft.Container(
        bgcolor=C["SURF"],
        padding=padding,
        border_radius=12,
        content=child,
        expand=expand,
    )

def metric_card(page: ft.Page, title: str, value: str):
    C = color_tokens(page)
    return card(
        page,
        ft.Column(
            [
                ft.Text(title, size=12, color=C["ON_SURF"], opacity=0.8),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
            ],
            spacing=6,
            tight=True,
        ),
    )

def draw_bar_chart(page: ft.Page, data: list[tuple[str, int]]):
    """Desenha um gráfico de barras simples usando containers (sem canvas)."""
    if not data:
        return ft.Text("Sem dados para o gráfico.")
    
    maxv = max(v for _, v in data) or 1
    C = color_tokens(page)
    
    # Criar barras usando containers simples
    bars = []
    for label, val in data:
        height = int(200 * (val / maxv)) or 10
        bar = ft.Container(
            width=60,
            height=height,
            bgcolor=C["PRIMARY"],
            border_radius=4,
            margin=8,
            content=ft.Column([
                ft.Text(str(val), size=10, color=C["ON_PRIMARY"], weight=ft.FontWeight.BOLD),
                ft.Text(label[:8], size=8, color=C["ON_SURF"]),
            ], spacing=4)
        )
        bars.append(bar)
    
    return card(page, ft.Row(controls=bars), padding=16)

# ---------------------- Main UI ----------------------
def build_ui(page: ft.Page):
    # Verificação de compatibilidade
    warnings = check_compatibility()
    if warnings:
        print(f"⚠️ Avisos de compatibilidade: {', '.join(warnings)}")
    
    # Tema
    page.title = "Garimpeiro Geek - Premium Dashboard"
    page.theme = ft.Theme(color_scheme_seed="#10b981")  # verde elegante
    page.theme_mode = ft.ThemeMode.DARK if os.getenv("DARK","1")=="1" else ft.ThemeMode.LIGHT
    
    # Força atualização do tema antes de acessar propriedades
    page.update()
    
    # Aguarda um pouco para o tema ser aplicado
    import time
    time.sleep(0.1)
    
    # Define cor de fundo com fallback seguro
    page.bgcolor = getattr(page.theme.color_scheme, 'background', '#ffffff') if page.theme.color_scheme else '#ffffff'

    C = color_tokens(page)

    # Estado de filtro / paginação
    page.session.set("window", "24h")      # 24h, 7d, 30d, tudo
    page.session.set("page", 1)
    PAGE_SIZE = 20

    conn = open_conn()
    table, mapping = (None, {})
    demo_mode = False
    if conn:
        table, mapping = find_table_and_cols(conn)
    if not conn or not table:
        demo_mode = True

    def since_from_window():
        w = page.session.get("window")
        now = dt.datetime.now()
        if w == "24h":
            return now - dt.timedelta(hours=24)
        if w == "7d":
            return now - dt.timedelta(days=7)
        if w == "30d":
            return now - dt.timedelta(days=30)
        return None

    # Header / AppBar
    def toggle_theme(_):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        page.bgcolor = getattr(page.theme.color_scheme, 'background', '#ffffff') if page.theme.color_scheme else '#ffffff'
        page.appbar.bgcolor = getattr(page.theme.color_scheme, 'surface', '#f5f5f5') if page.theme.color_scheme else '#f5f5f5'
        refresh()  # repinta cards com nova paleta
        page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("Garimpeiro Geek - Premium Dashboard", weight=ft.FontWeight.W_600),
        bgcolor=C["SURF"],
        center_title=False,
        actions=[ft.IconButton(get_theme_icon(page.theme_mode==ft.ThemeMode.DARK), on_click=toggle_theme)],
    )

    # Cards de métricas (usando Row simples para compatibilidade)
    metrics_row = ft.Row(spacing=12, wrap=True)

    # Chips de filtro (usando botões simples para compatibilidade)
    chips = ft.Row(
        controls=[
            ft.ElevatedButton("24h", on_click=lambda e: set_window("24h", e), bgcolor=C["PRIMARY"], color=C["ON_PRIMARY"]),
            ft.ElevatedButton("7 dias", on_click=lambda e: set_window("7d", e)),
            ft.ElevatedButton("30 dias", on_click=lambda e: set_window("30d", e)),
            ft.ElevatedButton("Tudo", on_click=lambda e: set_window("tudo", e)),
        ],
        spacing=8,
    )

    # Gráfico
    chart_area = ft.Column()

    # Tabela paginada
    table_title = ft.Text("Ofertas", size=16, weight=ft.FontWeight.W_600)
    tbl = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Data/Hora")),
            ft.DataColumn(ft.Text("Título")),
            ft.DataColumn(ft.Text("Loja")),
            ft.DataColumn(ft.Text("Preço")),
            ft.DataColumn(ft.Text("Link")),
        ],
        rows=[],
        heading_row_color=C["SURF"],
        data_row_max_height=56,
        column_spacing=18,
    )
    pager = ft.Row(spacing=8)

    def set_window(win: str, e: ft.ControlEvent):
        # Marcar botão ativo
        for i, (btn, key) in enumerate(zip(chips.controls, ["24h","7d","30d","tudo"])):
            if key == win:
                btn.bgcolor = C["PRIMARY"]
                btn.color = C["ON_PRIMARY"]
            else:
                btn.bgcolor = None
                btn.color = None
        page.session.set("window", win)
        page.session.set("page", 1)
        refresh()

    def goto_page(delta: int):
        p = page.session.get("page") + delta
        if p < 1: 
            return
        page.session.set("page", p)
        refresh()

    # Área principal (tabs)
    logs_lv = ft.ListView(expand=True, auto_scroll=True, spacing=4, padding=6)
    tabs = ft.Tabs(
        expand=1,
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Métricas",
                content=ft.Column(
                    [
                        metrics_row,
                        card(page, ft.Column([ft.Text("Filtros"), chips], spacing=8)),
                        card(page, chart_area),
                        ft.Divider(height=1, color=C["OUTLINE"]),
                        ft.Row([table_title]),
                        card(page, tbl, expand=False),
                        pager,
                    ],
                    spacing=12,
                    expand=True,
                ),
            ),
            ft.Tab(text="Logs", content=card(page, logs_lv, expand=True)),
        ],
    )
    page.add(tabs)

    # Logger de conveniência na aba Logs
    def log(msg: str):
        logs_lv.controls.append(ft.Text(msg, size=12))
        logs_lv.update()

    # Refresh geral
    def refresh():
        nonlocal conn, table, mapping, demo_mode
        C.update(color_tokens(page))
        # Cards
        metrics_row.controls.clear()
        w = since_from_window()

        if demo_mode:
            # Dados fake
            metrics = {"total": 127, "stores": 5, "avg_price": 199.9}
            by_store = [("Loja A", 45), ("Loja B", 33), ("Loja C", 20), ("Loja D", 18), ("Loja E", 11)]
            total_count = 127
            rows = [
                (dt.datetime.now().isoformat(" ", "seconds"), "Produto Exemplo", "Loja A", 199.9, "https://exemplo")
                for _ in range(20)
            ]
            log("Aviso: Banco não detectado. Exibindo dados de demonstração.")
        else:
            try:
                metrics = get_metrics(conn, table, mapping, w)
                by_store = offers_by_store(conn, table, mapping, w, limit=10)
                total_count = count_offers(conn, table, mapping, w)
                rows = fetch_offers(conn, table, mapping, page.session.get("page"), PAGE_SIZE, w)
            except Exception as ex:
                demo_mode = True
                log(f"Erro no banco: {ex}. Entrando em modo demo.")
                refresh()
                return

        avg_disp = f"R$ {metrics['avg_price']:.2f}" if metrics["avg_price"] else "--"
        metrics_row.controls.extend([
            ft.Container(content=metric_card(page, "Ofertas (janela)", str(metrics["total"])), width=200),
            ft.Container(content=metric_card(page, "Lojas ativas", str(metrics["stores"])), width=200),
            ft.Container(content=metric_card(page, "Preço médio", avg_disp), width=200),
            ft.Container(content=metric_card(page, "Página atual", str(page.session.get("page"))), width=200),
        ])
        metrics_row.update()

        # Gráfico
        chart_area.controls.clear()
        chart_area.controls.append(draw_bar_chart(page, by_store))
        chart_area.update()

        # Tabela
        tbl.rows.clear()
        for created, title, store, price, url in rows:
            link_ctrl = ft.TextButton("abrir", url=url) if url else ft.Text("--")
            try:
                pdisp = f"R$ {float(price):.2f}"
            except Exception:
                pdisp = str(price)
            tbl.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(created)[:19])),
                    ft.DataCell(ft.Text(str(title))),
                    ft.DataCell(ft.Text(str(store))),
                    ft.DataCell(ft.Text(pdisp)),
                    ft.DataCell(link_ctrl),
                ])
            )
        tbl.update()

        # Paginação
        total_pages = max(1, math.ceil(total_count / PAGE_SIZE))
        cur = page.session.get("page")
        pager.controls.clear()
        pager.controls.extend([
            ft.OutlinedButton("« Anterior", on_click=lambda e: goto_page(-1), disabled=(cur<=1)),
            ft.Text(f"Página {cur} de {total_pages}"),
            ft.OutlinedButton("Próxima »", on_click=lambda e: goto_page(+1), disabled=(cur>=total_pages)),
        ])
        pager.update()

    refresh()
    log("Premium Dashboard pronto.")

# ---------------------- Entrypoint / CLI ----------------------
def _target(page: ft.Page):
    return build_ui(page)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("DASHBOARD_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=os.getenv("DASHBOARD_PORT", "8550"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--desktop", action="store_true", help="abre como app nativo (janela)")
    args = parser.parse_args()

    if args.desktop:
        ft.app(target=_target, view=ft.AppView.FLET_APP)
    else:
        view = None if args.headless or os.getenv("DASHBOARD_HEADLESS","0")=="1" else ft.AppView.WEB_BROWSER
        ft.app(target=_target, host=args.host, port=args.port, view=view)

if __name__ == "__main__":
    main()
