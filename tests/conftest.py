# tests/conftest.py
import os
import pytest

def pytest_configure():
    """Configuração do pytest para evitar envios acidentais ao Telegram"""
    # Evita que testes tentem postar no Telegram acidentalmente
    os.environ.setdefault("DRY_RUN", "1")
    print("🔒 Modo DRY_RUN ativado - nenhuma mensagem será enviada ao Telegram")

@pytest.fixture(scope="session", autouse=True)
def ensure_reports_dir():
    """Garante que o diretório reports existe"""
    os.makedirs("reports", exist_ok=True)
    print("📁 Diretório reports verificado/criado")

@pytest.fixture(scope="session")
def test_environment():
    """Configuração do ambiente de teste"""
    return {
        "dry_run": True,
        "max_offers_per_scraper": 5,
        "test_timeout": 30
    }
