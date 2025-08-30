"""
Testes para utilitários anti-bot
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.anti_bot import AntiBotUtils, anti_bot_utils


class TestAntiBotUtils(unittest.TestCase):
    """Testes para AntiBotUtils"""

    def test_user_agents_rotation(self):
        """Testa rotação de User-Agents"""
        utils = AntiBotUtils()

        # Verificar se tem User-Agents válidos
        self.assertGreater(len(utils.USER_AGENTS), 0)

        # Verificar se são diferentes
        agents = set()
        for _ in range(10):
            agents.add(utils.get_random_headers()["User-Agent"])

        # Deve ter pelo menos alguns User-Agents diferentes
        self.assertGreater(len(agents), 1)

    def test_default_headers(self):
        """Testa headers padrão"""
        utils = AntiBotUtils()
        headers = utils.get_random_headers()

        # Verificar headers obrigatórios
        required_headers = ["User-Agent", "Accept", "Accept-Language"]
        for header in required_headers:
            self.assertIn(header, headers)
            self.assertTrue(headers[header])

    def test_domain_extraction(self):
        """Testa extração de domínio"""
        utils = AntiBotUtils()

        test_cases = [
            ("https://www.kabum.com.br/produto/123", "www.kabum.com.br"),
            ("http://amazon.com.br/produto", "amazon.com.br"),
            ("https://shopee.com.br/", "shopee.com.br"),
            ("invalid-url", ""),
        ]

        for url, expected_domain in test_cases:
            domain = utils.get_domain_from_url(url)
            self.assertEqual(domain, expected_domain)

    def test_rate_limit_detection(self):
        """Testa detecção de rate limiting"""
        utils = AntiBotUtils()

        # Mock de resposta
        mock_response = MagicMock()

        # Testar status codes de rate limit
        for status in [429, 503, 502]:
            mock_response.status = status
            self.assertTrue(utils.is_rate_limited(mock_response))

        # Testar status codes normais
        for status in [200, 404, 500]:
            mock_response.status = status
            self.assertFalse(utils.is_rate_limited(mock_response))

    @patch("src.utils.anti_bot.aiohttp.ClientSession")
    async def test_session_creation(self, mock_session_class):
        """Testa criação de sessão HTTP"""
        utils = AntiBotUtils()

        # Mock da sessão
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        # Obter sessão
        session = await utils.get_session()

        # Verificar se foi criada
        self.assertEqual(session, mock_session)
        mock_session_class.assert_called_once()

    def test_anti_bot_utils_global(self):
        """Testa instância global"""
        # Verificar se existe
        self.assertIsInstance(anti_bot_utils, AntiBotUtils)

        # Verificar se tem métodos necessários
        self.assertTrue(hasattr(anti_bot_utils, "get_random_headers"))
        self.assertTrue(hasattr(anti_bot_utils, "get_domain_from_url"))
        self.assertTrue(hasattr(anti_bot_utils, "is_rate_limited"))


if __name__ == "__main__":
    unittest.main()
