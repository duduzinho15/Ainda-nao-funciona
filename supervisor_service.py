# supervisor_service.py
import asyncio, os, sys, time, socket, subprocess, pathlib, shutil
from pathlib import Path
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Carrega variáveis de ambiente
load_dotenv(ROOT / ".env")

# Forçar UTF-8 para subprocessos
BASE_ENV = os.environ.copy()
BASE_ENV.setdefault("PYTHONIOENCODING", "utf-8")

def port_in_use(host: str, port: int) -> bool:
    """Verifica se uma porta está ocupada"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex((host, port)) == 0
    except:
        return False

def should_skip_restart(stderr_tail: str) -> bool:
    """Detecta erros não-recuperáveis para evitar restart"""
    text = (stderr_tail or "").lower()
    needles = [
        "winerror 10048",
        "address already in use",
        "bind on address",
        "unicodeencodeerror",
        "charmap codec can't encode",
    ]
    return any(n in text for n in needles)

async def run_and_supervise(name: str, cmd: list[str], logfile_prefix: str,
                            max_restarts: int = 3, window_seconds: int = 120):
    """
    Supervisiona um processo com política anti-loop:
    - Máximo de 'max_restarts' em 'window_seconds'.
    - Se crashar imediatamente (<3s), conta como candidato a loop.
    - Se stderr indicar porta ocupada/encoding, NÃO reinicia.
    """
    restarts = []
    while True:
        # Limpa janela antiga
        now = time.time()
        restarts = [t for t in restarts if now - t <= window_seconds]
        if len(restarts) >= max_restarts:
            print(f"[supervisor] {name}: limite de reinícios atingido ({max_restarts}/{window_seconds}s). Abortando.")
            return

        # Arquivos de log
        out_path = LOGS_DIR / f"{logfile_prefix}.out.log"
        err_path = LOGS_DIR / f"{logfile_prefix}.err.log"

        print(f"[supervisor] iniciando {name}: {' '.join(cmd)}")
        start_ts = time.time()
        
        with open(out_path, "ab", buffering=0) as f_out, open(err_path, "ab", buffering=0) as f_err:
            f_out.write(b"\n--- start ---\n")
            f_err.write(b"\n--- start ---\n")

            proc = subprocess.Popen(
                cmd,
                stdout=f_out,
                stderr=f_err,
                env=BASE_ENV,
                cwd=str(ROOT),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            rc = None
            try:
                while True:
                    rc = proc.poll()
                    if rc is not None:
                        break
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                raise

        duration = time.time() - start_ts
        if rc == 0:
            print(f"[supervisor] {name} terminou normalmente (rc=0). Encerrando supervisão.")
            return

        # Lê cauda do stderr p/ tomada de decisão
        tail = ""
        try:
            with open(err_path, "rb") as f:
                f.seek(max(0, f.tell() - 4096))
                tail = f.read().decode("utf-8", errors="ignore")[-1500:]
        except Exception:
            pass

        print(f"[supervisor] {name} saiu com rc={rc} após {duration:.1f}s")
        if should_skip_restart(tail):
            print(f"[supervisor] {name}: causa não-recuperável detectada. NÃO reiniciar.")
            return

        if duration < 3.0:
            restarts.append(time.time())

        backoff = min(60, 2 ** max(1, len(restarts)))
        print(f"[supervisor] reiniciando {name} em {backoff}s...")
        await asyncio.sleep(backoff)

async def main():
    host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.getenv("DASHBOARD_PORT", "8550"))
    headless = os.getenv("DASHBOARD_HEADLESS", "1") == "1"

    python = shutil.which("python") or sys.executable
    venv_python = os.getenv("VENV_PYTHON") or str((ROOT / ".venv" / "Scripts" / "python.exe"))

    bot_cmd = [venv_python, "main_simples.py"]  # ajuste aqui se for test_bot_simple.py
    dash_cmd = [venv_python, "-m", "flet_app.main", "--host", host, "--port", str(port)]
    if headless:
        dash_cmd.append("--headless")

    print("[supervisor] Iniciando...")
    print(f"[supervisor] Dashboard: {'Sim' if headless else 'NÃO-headless'} | Host: {host}:{port} | Headless: {headless}")

    tasks = []

    # Inicia BOT (sempre)
    tasks.append(asyncio.create_task(run_and_supervise("bot", bot_cmd, "bot")))

    # Inicia DASHBOARD somente se porta livre
    if os.getenv("DASHBOARD_ENABLED", "1") == "1":
        if port_in_use(host, port):
            print(f"[supervisor] Porta {host}:{port} ocupada. NÃO iniciaremos outro dashboard.")
        else:
            tasks.append(asyncio.create_task(run_and_supervise("dashboard", dash_cmd, "dashboard")))
    else:
        print("[supervisor] Dashboard desabilitado (DASHBOARD_ENABLED=0).")

    # Espera CTRL+C
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("[supervisor] Interrompido pelo usuário.")

if __name__ == "__main__":
    asyncio.run(main())
