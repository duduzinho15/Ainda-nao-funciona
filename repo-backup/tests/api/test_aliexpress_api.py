"""
Testes unitários para o cliente AliExpress API
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.affiliate.aliexpress_api_client import AliExpressAPIClient


class TestAliExpressAPIClient:
    """Testes para AliExpressAPIClient"""

    @pytest.fixture
    def client(self):
        """Cliente de teste"""
        return AliExpressAPIClient(
            app_key="test_key", app_secret="test_secret", access_token="test_token"
        )

    @pytest.fixture
    def mock_session(self):
        """Sessão mockada"""
        return Mock()

    def test_init(self, client):
        """Testa inicialização do cliente"""
        assert client.app_key == "test_key"
        assert client.app_secret == "test_secret"
        assert client.access_token == "test_token"
        assert client.api_version == "2.0"
        assert client.sign_method == "sha256"

    def test_generate_signature(self, client):
        """Testa geração de assinatura"""
        params = {
            "method": "test.method",
            "app_key": "test_key",
            "timestamp": "2024-01-01 12:00:00",
        }

        signature = client._generate_signature(params)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex
        assert signature.isupper()  # Deve ser maiúsculo

    def test_prepare_request_params(self, client):
        """Testa preparação de parâmetros da requisição"""
        method = "test.method"
        params = {"param1": "value1"}

        request_params = client._prepare_request_params(method, params)

        assert "method" in request_params
        assert "app_key" in request_params
        assert "timestamp" in request_params
        assert "sign" in request_params
        assert request_params["method"] == method
        assert request_params["param1"] == "value1"

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, client):
        """Testa obtenção de token de acesso com sucesso"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"access_token": "new_token", "expires_in": 7200}
        )

        with patch.object(client, "session") as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            token = await client.get_access_token()

            assert token == "new_token"
            assert client.access_token == "new_token"
            assert client.token_expires_at is not None

    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, client):
        """Testa falha na obtenção de token"""
        mock_response = Mock()
        mock_response.status = 401

        with patch.object(client, "session") as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            token = await client.get_access_token()

            assert token is None

    @pytest.mark.asyncio
    async def test_refresh_token_not_expired(self, client):
        """Testa renovação de token não expirado"""
        client.token_expires_at = datetime.now() + timedelta(hours=1)

        token = await client.refresh_token()

        assert token is True

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, client):
        """Testa renovação de token expirado"""
        client.token_expires_at = datetime.now() - timedelta(hours=1)

        with patch.object(client, "get_access_token", return_value="new_token"):
            token = await client.refresh_token()

            assert token is True

    @pytest.mark.asyncio
    async def test_generate_affiliate_link_success(self, client):
        """Testa geração de link de afiliado com sucesso"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"affiliate_url": "https://s.click.aliexpress.com/test"}
        )

        with patch.object(client, "refresh_token", return_value=True), patch.object(
            client, "session"
        ) as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            affiliate_url = await client.generate_affiliate_link(
                url="https://example.com/product", tracking_id="test"
            )

            assert affiliate_url == "https://s.click.aliexpress.com/test"

    @pytest.mark.asyncio
    async def test_search_products_success(self, client):
        """Testa busca de produtos com sucesso"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "products": [
                    {"product_id": "1", "title": "Product 1"},
                    {"product_id": "2", "title": "Product 2"},
                ]
            }
        )

        with patch.object(client, "refresh_token", return_value=True), patch.object(
            client, "session"
        ) as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            products = await client.search_products(
                query="smartphone",
                limit=10,
                ship_to_country="BR",
                currency="BRL",
                language="pt",
            )

            assert len(products) == 2
            assert products[0]["product_id"] == "1"
            assert products[1]["title"] == "Product 2"

    @pytest.mark.asyncio
    async def test_get_hot_products_success(self, client):
        """Testa obtenção de produtos em alta com sucesso"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "hot_products": [
                    {"product_id": "1", "title": "Hot Product 1"},
                    {"product_id": "2", "title": "Hot Product 2"},
                ]
            }
        )

        with patch.object(client, "refresh_token", return_value=True), patch.object(
            client, "session"
        ) as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            products = await client.get_hot_products(limit=10)

            assert len(products) == 2
            assert products[0]["title"] == "Hot Product 1"

    @pytest.mark.asyncio
    async def test_get_product_details_success(self, client):
        """Testa obtenção de detalhes do produto com sucesso"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "product": {
                    "product_id": "123",
                    "title": "Test Product",
                    "price": 99.99,
                }
            }
        )

        with patch.object(client, "refresh_token", return_value=True), patch.object(
            client, "session"
        ) as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            product = await client.get_product_details("123")

            assert product["product_id"] == "123"
            assert product["title"] == "Test Product"
            assert product["price"] == 99.99

    @pytest.mark.asyncio
    async def test_get_smart_match_products_success(self, client):
        """Testa smart match de produtos com sucesso"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "similar_products": [
                    {"product_id": "1", "title": "Similar 1"},
                    {"product_id": "2", "title": "Similar 2"},
                ]
            }
        )

        with patch.object(client, "refresh_token", return_value=True), patch.object(
            client, "session"
        ) as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            products = await client.get_smart_match_products(
                image_url="https://example.com/image.jpg"
            )

            assert len(products) == 2
            assert products[0]["title"] == "Similar 1"

    def test_get_stats(self, client):
        """Testa obtenção de estatísticas"""
        stats = client.get_stats()

        assert "app_key_configured" in stats
        assert "app_secret_configured" in stats
        assert "access_token_valid" in stats
        assert "api_version" in stats
        assert "sign_method" in stats

        assert stats["app_key_configured"] is True
        assert stats["app_secret_configured"] is True
        assert stats["access_token_valid"] is True
        assert stats["api_version"] == "2.0"
        assert stats["sign_method"] == "sha256"


class TestAliExpressAPIClientIntegration:
    """Testes de integração para AliExpressAPIClient"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Testa workflow completo do cliente"""
        client = AliExpressAPIClient(app_key="test_key", app_secret="test_secret")

        # Mock das respostas da API
        mock_token_response = Mock()
        mock_token_response.status = 200
        mock_token_response.json = AsyncMock(
            return_value={"access_token": "test_token", "expires_in": 7200}
        )

        mock_search_response = Mock()
        mock_search_response.status = 200
        mock_search_response.json = AsyncMock(
            return_value={
                "products": [
                    {
                        "product_id": "123",
                        "title": "Test Product",
                        "price": 99.99,
                        "product_url": "https://example.com/product",
                    }
                ]
            }
        )

        mock_link_response = Mock()
        mock_link_response.status = 200
        mock_link_response.json = AsyncMock(
            return_value={"affiliate_url": "https://s.click.aliexpress.com/test"}
        )

        with patch.object(client, "session") as mock_session:
            # Configurar mocks para diferentes chamadas
            mock_session.post.side_effect = [
                mock_token_response,  # get_access_token
                mock_search_response,  # search_products
                mock_link_response,  # generate_affiliate_link
            ]

            # Executar workflow
            token = await client.get_access_token()
            assert token == "test_token"

            products = await client.search_products("test")
            assert len(products) == 1

            affiliate_url = await client.generate_affiliate_link(
                url="https://example.com/product"
            )
            assert affiliate_url == "https://s.click.aliexpress.com/test"

    def test_signature_consistency(self):
        """Testa consistência da assinatura"""
        client = AliExpressAPIClient(app_key="test_key", app_secret="test_secret")

        params = {
            "method": "test.method",
            "app_key": "test_key",
            "timestamp": "2024-01-01 12:00:00",
        }

        # Gerar assinatura múltiplas vezes
        signature1 = client._generate_signature(params)
        signature2 = client._generate_signature(params)

        # Deve ser idêntica para os mesmos parâmetros
        assert signature1 == signature2

    def test_parameter_ordering(self):
        """Testa ordenação de parâmetros para assinatura"""
        client = AliExpressAPIClient(app_key="test_key", app_secret="test_secret")

        # Parâmetros em ordem diferente
        params1 = {"b": "2", "a": "1", "c": "3"}
        params2 = {"c": "3", "a": "1", "b": "2"}

        # Deve gerar a mesma assinatura
        signature1 = client._generate_signature(params1)
        signature2 = client._generate_signature(params2)

        assert signature1 == signature2


# Testes de erro e edge cases
class TestAliExpressAPIClientErrorHandling:
    """Testes de tratamento de erro para AliExpressAPIClient"""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Testa tratamento de erros de rede"""
        client = AliExpressAPIClient(app_key="test_key", app_secret="test_secret")

        with patch.object(client, "session") as mock_session:
            mock_session.post.side_effect = Exception("Network error")

            # Deve retornar None em caso de erro
            token = await client.get_access_token()
            assert token is None

    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Testa tratamento de resposta JSON inválida"""
        client = AliExpressAPIClient(app_key="test_key", app_secret="test_secret")

        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=Exception("Invalid JSON"))

        with patch.object(client, "refresh_token", return_value=True), patch.object(
            client, "session"
        ) as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response

            # Deve retornar lista vazia em caso de erro
            products = await client.search_products("test")
            assert products == []

    def test_empty_parameters(self):
        """Testa comportamento com parâmetros vazios"""
        client = AliExpressAPIClient(app_key="test_key", app_secret="test_secret")

        # Deve funcionar com parâmetros vazios
        signature = client._generate_signature({})
        assert isinstance(signature, str)
        assert len(signature) == 64


@pytest.mark.asyncio
async def test_alix_generate_link_mock(monkeypatch):
    class DummyAliX:
        async def generate_affiliate_link(self, product_id: str, tracking_id: str):
            assert product_id.isdigit() or product_id
            return {
                "promotion_link": "https://s.click.aliexpress.com/e/_abc123",
                "tracking_id": tracking_id,
            }

    cli = DummyAliX()
    res = await cli.generate_affiliate_link("1005006756452012", "telegram")
    assert res["promotion_link"].startswith("https://s.click.aliexpress.com/e/")
    assert res["tracking_id"] == "telegram"
