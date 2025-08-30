"""
Testes para validação dos schemas dos bancos de dados
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.db_init import DatabaseInitializer


class TestDatabaseSchemas(unittest.TestCase):
    """Testes para validação dos schemas"""

    def setUp(self):
        """Configuração antes de cada teste"""
        # Usar bancos temporários para testes
        self.temp_dir = tempfile.mkdtemp()
        self.temp_aff_cache = Path(self.temp_dir) / "aff_cache.sqlite"
        self.temp_analytics = Path(self.temp_dir) / "analytics.sqlite"

        # Mock dos caminhos dos bancos
        self.db_config_patcher = patch(
            "src.core.db_init.DB_CONFIG",
            {
                "aff_cache": str(self.temp_aff_cache),
                "analytics": str(self.temp_analytics),
            },
        )
        self.db_config_patcher.start()

        self.initializer = DatabaseInitializer()

    def tearDown(self):
        """Limpeza após cada teste"""
        self.db_config_patcher.stop()

        # Remover bancos temporários
        try:
            if self.temp_aff_cache.exists():
                self.temp_aff_cache.unlink()
            if self.temp_analytics.exists():
                self.temp_analytics.unlink()
        except Exception:
            pass

        # Remover diretório temporário
        try:
            import shutil

            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_aff_cache_schema_creation(self):
        """Testa criação do schema do banco aff_cache"""
        # Inicializar banco
        success = self.initializer.init_database("aff_cache")
        self.assertTrue(success)

        # Verificar se o banco foi criado
        self.assertTrue(self.temp_aff_cache.exists())

        # Verificar se as tabelas foram criadas
        validation = self.initializer.validate_schemas()
        aff_cache_validation = validation["aff_cache"]

        self.assertTrue(aff_cache_validation["exists"])
        self.assertFalse(aff_cache_validation["errors"])

        # Verificar tabela shortlinks
        self.assertTrue(aff_cache_validation["tables"]["shortlinks"])

    def test_analytics_schema_creation(self):
        """Testa criação do schema do banco analytics"""
        # Inicializar banco
        success = self.initializer.init_database("analytics")
        self.assertTrue(success)

        # Verificar se o banco foi criado
        self.assertTrue(self.temp_analytics.exists())

        # Verificar se as tabelas foram criadas
        validation = self.initializer.validate_schemas()
        analytics_validation = validation["analytics"]

        self.assertTrue(analytics_validation["exists"])
        self.assertFalse(analytics_validation["errors"])

        # Verificar tabelas principais
        expected_tables = [
            "products",
            "price_history",
            "price_daily",
            "external_product_map",
            "external_price_points",
            "external_price_daily",
            "perf",
            "offers_posted",
            "revenue",
        ]

        for table in expected_tables:
            self.assertTrue(analytics_validation["tables"][table])

    def test_all_databases_initialization(self):
        """Testa inicialização de todos os bancos"""
        results = self.initializer.init_all_databases()

        # Verificar se todos os bancos foram inicializados
        self.assertTrue(all(results.values()))

        # Verificar se os bancos existem
        self.assertTrue(self.temp_aff_cache.exists())
        self.assertTrue(self.temp_analytics.exists())

    def test_schema_validation(self):
        """Testa validação dos schemas"""
        # Primeiro inicializar os bancos
        self.initializer.init_all_databases()

        # Validar schemas
        validation = self.initializer.validate_schemas()

        # Verificar se não há erros
        for db_name, result in validation.items():
            self.assertFalse(
                result["errors"], f"Erros encontrados em {db_name}: {result['errors']}"
            )

    def test_expected_tables(self):
        """Testa se todas as tabelas esperadas foram criadas"""
        # Inicializar bancos
        self.initializer.init_all_databases()

        # Verificar tabelas do aff_cache
        aff_cache_tables = self.initializer._get_expected_tables("aff_cache")
        self.assertEqual(aff_cache_tables, ["shortlinks"])

        # Verificar tabelas do analytics
        analytics_tables = self.initializer._get_expected_tables("analytics")
        expected_analytics = [
            "products",
            "price_history",
            "price_daily",
            "external_product_map",
            "external_price_points",
            "external_price_daily",
            "perf",
            "offers_posted",
            "revenue",
        ]
        self.assertEqual(analytics_tables, expected_analytics)

    def test_schema_version(self):
        """Testa versão do schema"""
        version = self.initializer.get_schema_version()
        self.assertEqual(version, "1.0.0")

    def test_database_directory_creation(self):
        """Testa criação automática de diretórios"""
        # Usar caminho com diretório que não existe
        temp_db_path = Path(self.temp_dir) / "nested" / "test.sqlite"

        # Verificar se o diretório não existe inicialmente
        self.assertFalse(temp_db_path.parent.exists())

        # Criar diretório manualmente para testar
        temp_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Verificar se o diretório foi criado
        self.assertTrue(temp_db_path.parent.exists())

    def test_invalid_database_name(self):
        """Testa inicialização com nome de banco inválido"""
        success = self.initializer.init_database("invalid_db")
        self.assertFalse(success)

    def test_schema_validation_without_databases(self):
        """Testa validação quando bancos não existem"""
        # Validar sem inicializar
        validation = self.initializer.validate_schemas()

        for _db_name, result in validation.items():
            self.assertFalse(result["exists"])
            self.assertIn("Banco não existe", result["errors"])


if __name__ == "__main__":
    unittest.main()
