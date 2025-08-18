# tests/conftest.py
import os
import pytest


def pytest_configure():
    """Configuração do pytest para evitar postagem acidental no Telegram"""
    # Evita que testes tentem postar no Telegram acidentalmente
    os.environ.setdefault("DRY_RUN", "1")
    os.environ.setdefault("TEST_MODE", "1")


@pytest.fixture(scope="session", autouse=True)
def ensure_reports_dir():
    """Garante que a pasta reports existe"""
    os.makedirs("reports", exist_ok=True)


@pytest.fixture(scope="session")
def test_environment():
    """Configuração do ambiente de teste"""
    return {"dry_run": True, "test_mode": True, "max_offers_per_scraper": 5}
