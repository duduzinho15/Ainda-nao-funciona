"""
Testes para módulos core do sistema
"""

import tempfile
from pathlib import Path

import pytest

from src.core.affiliate_converter import AffiliateConverter
from src.core.database import Database
from src.core.live_logs import LiveLogReader
from src.core.metrics import Metrics, MetricsCollector
from src.core.storage import PreferencesStorage


class TestPreferencesStorage:
    """Testes para o sistema de preferências"""

    def setup_method(self):
        """Configuração antes de cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = PreferencesStorage(self.temp_dir)

    def teardown_method(self):
        """Limpeza após cada teste"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_default_preferences(self):
        """Testa se as preferências padrão são carregadas"""
        assert self.storage.get_preference("theme") == "dark"
        assert self.storage.get_preference("language") == "pt_BR"
        assert self.storage.get_preference("last_period") == "7d"

    def test_set_and_get_preference(self):
        """Testa definição e obtenção de preferências"""
        self.storage.set_preference("test_key", "test_value")
        assert self.storage.get_preference("test_key") == "test_value"

    def test_save_and_load_preferences(self):
        """Testa salvamento e carregamento de preferências"""
        self.storage.set_preference("custom_key", "custom_value")

        # Criar nova instância para testar carregamento
        new_storage = PreferencesStorage(self.temp_dir)
        assert new_storage.get_preference("custom_key") == "custom_value"

    def test_reset_preferences(self):
        """Testa reset das preferências"""
        self.storage.set_preference("test_key", "test_value")
        self.storage.reset_preferences()
        assert self.storage.get_preference("test_key") != "test_value"


class TestDatabase:
    """Testes para o sistema de banco de dados"""

    def setup_method(self):
        """Configuração antes de cada teste"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
        self.db = Database(self.temp_db.name)

    def teardown_method(self):
        """Limpeza após cada teste"""
        try:
            if hasattr(self, 'db') and self.db:
                self.db.close()
        except Exception:
            pass

        try:
            if hasattr(self, 'temp_db') and self.temp_db:
                # Aguardar um pouco para garantir que o arquivo seja liberado
                import time
                time.sleep(0.1)
                Path(self.temp_db.name).unlink(missing_ok=True)
        except Exception:
            pass

    def test_database_initialization(self):
        """Testa inicialização do banco"""
        assert self.db.connection is not None

    def test_insert_and_get_oferta(self):
        """Testa inserção e obtenção de ofertas"""
        oferta = {
            "titulo": "Teste",
            "preco": 99.99,
            "loja": "Teste Store",
            "url": "https://teste.com",
        }

        oferta_id = self.db.insert_oferta(oferta)
        assert oferta_id > 0

        ofertas = self.db.get_ofertas()
        assert len(ofertas) > 0
        assert ofertas[0]["titulo"] == "Teste"


class TestMetrics:
    """Testes para o sistema de métricas"""

    def setup_method(self):
        """Configuração antes de cada teste"""
        self.metrics = Metrics(100, 5, 50.0)

    def test_metrics_creation(self):
        """Testa criação de métricas"""
        assert self.metrics.total_ofertas == 100
        assert self.metrics.lojas_ativas == 5
        assert self.metrics.preco_medio == 50.0

    def test_preco_medio_formatado(self):
        """Testa formatação do preço médio"""
        formatted = self.metrics.preco_medio_formatado()
        assert "R$" in formatted
        assert "50,00" in formatted

    def test_metrics_collector(self):
        """Testa o coletor de métricas"""
        collector = MetricsCollector()
        collector.update_metrics(200, 10, 75.0)

        current = collector.get_current_metrics()
        assert current.total_ofertas == 200
        assert current.lojas_ativas == 10
        assert current.preco_medio == 75.0


class TestLiveLogReader:
    """Testes para o sistema de logs em tempo real"""

    def setup_method(self):
        """Configuração antes de cada teste"""
        self.log_reader = LiveLogReader()

    def test_add_log(self):
        """Testa adição de logs"""
        self.log_reader.add_log("INFO", "Teste de log", "teste")

        logs = self.log_reader.get_current_logs()
        assert len(logs) == 1
        assert logs[0]["mensagem"] == "Teste de log"
        assert logs[0]["nivel"] == "INFO"

    def test_log_buffer_limit(self):
        """Testa limite do buffer de logs"""
        # Adicionar mais logs que o limite
        for i in range(1500):
            self.log_reader.add_log("INFO", f"Log {i}", "teste")

        logs = self.log_reader.get_current_logs()
        assert len(logs) <= 1000  # max_lines padrão


class TestAffiliateConverter:
    """Testes para o conversor de links de afiliado"""

    def setup_method(self):
        """Configuração antes de cada teste"""
        self.converter = AffiliateConverter()

    def test_identify_store(self):
        """Testa identificação de lojas"""
        amazon_url = "https://amazon.com.br/produto"
        store = self.converter.identify_store(amazon_url)
        assert store == "amazon"

    def test_convert_to_affiliate(self):
        """Testa conversão para link de afiliado"""
        amazon_url = "https://amazon.com.br/produto"
        affiliate_url = self.converter.convert_to_affiliate(amazon_url)

        assert affiliate_url != amazon_url
        assert "tag=garimpeirogeek-20" in affiliate_url

    def test_unsupported_store(self):
        """Testa loja não suportada"""
        unsupported_url = "https://loja-inexistente.com/produto"
        affiliate_url = self.converter.convert_to_affiliate(unsupported_url)

        # Deve retornar a URL original sem modificação
        assert affiliate_url == unsupported_url


if __name__ == "__main__":
    pytest.main([__file__])
