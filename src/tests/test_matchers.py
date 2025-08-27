"""
Testes para o sistema de matching de produtos
"""

import unittest

from src.core.matchers import (
    ProductMatch,
    ProductMatcher,
    calculate_similarity,
    choose_best_match,
    extract_model,
    normalize_title,
)


class TestProductMatcher(unittest.TestCase):
    """Testes para ProductMatcher"""

    def setUp(self):
        """Configuração antes de cada teste"""
        self.matcher = ProductMatcher()

    def test_normalize_title(self):
        """Testa normalização de títulos"""
        # Teste básico
        normalized = self.matcher.normalize_title("iPhone 14 Pro Max 256GB")
        self.assertIn("iphone", normalized)
        self.assertIn("14", normalized)
        self.assertIn("pro", normalized)
        self.assertIn("max", normalized)
        self.assertIn("256gb", normalized)

        # Teste com caracteres especiais
        normalized = self.matcher.normalize_title('Monitor LG 34GP63A-B 34"')
        self.assertIn("monitor", normalized)
        self.assertIn("lg", normalized)
        self.assertIn("34gp63a", normalized)

        # Teste com stop words
        normalized = self.matcher.normalize_title("Cabo USB-C para iPhone 14")
        self.assertIn("cabo", normalized)
        self.assertIn("usb", normalized)
        self.assertIn("iphone", normalized)
        self.assertIn("14", normalized)
        self.assertNotIn("para", normalized)  # stop word removida

    def test_extract_model(self):
        """Testa extração de modelo"""
        # Teste padrões de modelo
        self.assertEqual(self.matcher.extract_model("LG 34GP63A-B"), "GP63A")
        self.assertEqual(self.matcher.extract_model("RTX-3080"), "RTX-3080")
        self.assertEqual(self.matcher.extract_model("iPhone 14 Pro"), "14PRO")
        self.assertEqual(self.matcher.extract_model("Galaxy S22 Ultra"), "22ULTRA")

        # Teste sem modelo
        self.assertIsNone(self.matcher.extract_model("Cabo USB-C"))
        self.assertIsNone(self.matcher.extract_model(""))

    def test_extract_brand(self):
        """Testa extração de marca"""
        # Teste marcas conhecidas
        self.assertEqual(self.matcher.extract_brand("iPhone 14 Pro"), "Apple")
        self.assertEqual(self.matcher.extract_brand("Samsung Galaxy S22"), "Samsung")
        self.assertEqual(self.matcher.extract_brand("LG Monitor"), "LG")
        self.assertEqual(self.matcher.extract_brand("ASUS TUF Gaming"), "Asus")

        # Teste sem marca conhecida
        self.assertIsNone(self.matcher.extract_brand("Cabo USB-C"))

    def test_calculate_similarity(self):
        """Testa cálculo de similaridade"""
        # Teste títulos idênticos
        similarity = self.matcher.calculate_similarity("iPhone 14 Pro", "iPhone 14 Pro")
        self.assertEqual(similarity, 1.0)

        # Teste títulos similares
        similarity = self.matcher.calculate_similarity(
            "iPhone 14 Pro", "iPhone 14 Pro Max"
        )
        self.assertGreater(similarity, 0.8)

        # Teste títulos diferentes
        similarity = self.matcher.calculate_similarity(
            "iPhone 14 Pro", "Samsung Galaxy S22"
        )
        self.assertLess(similarity, 0.5)

        # Teste com títulos vazios
        self.assertEqual(self.matcher.calculate_similarity("", "test"), 0.0)
        self.assertEqual(self.matcher.calculate_similarity("test", ""), 0.0)

    def test_is_restrictive_category(self):
        """Testa identificação de categorias restritivas"""
        # Teste categorias restritivas
        self.assertTrue(self.matcher.is_restrictive_category("Cabo USB-C"))
        self.assertTrue(self.matcher.is_restrictive_category("Película para iPhone"))
        self.assertTrue(self.matcher.is_restrictive_category("Case para Samsung"))

        # Teste categorias não restritivas
        self.assertFalse(self.matcher.is_restrictive_category("iPhone 14 Pro"))
        self.assertFalse(self.matcher.is_restrictive_category("Monitor LG"))

    def test_has_specific_keywords(self):
        """Testa identificação de palavras-chave específicas"""
        # Teste com palavras-chave específicas
        self.assertTrue(self.matcher.has_specific_keywords("iPhone 14 Pro"))
        self.assertTrue(self.matcher.has_specific_keywords("Samsung Galaxy S22"))
        self.assertTrue(self.matcher.has_specific_keywords("RTX 3080"))

        # Teste sem palavras-chave específicas
        self.assertFalse(self.matcher.has_specific_keywords("Cabo USB-C"))
        self.assertFalse(self.matcher.has_specific_keywords("Película para celular"))

    def test_choose_best_match_ean(self):
        """Testa escolha de melhor match por EAN/SKU"""
        candidates = [
            {
                "title": "Produto A",
                "url": "http://a.com",
                "source": "zoom",
                "sku": "12345",
            },
            {
                "title": "Produto B",
                "url": "http://b.com",
                "source": "buscape",
                "sku": "67890",
            },
        ]

        target_title = "Produto Teste"
        target_sku = "12345"

        match = self.matcher.choose_best_match(candidates, target_title, target_sku)

        self.assertIsNotNone(match)
        self.assertEqual(match.confidence, 1.0)
        self.assertEqual(match.match_type, "ean")
        self.assertEqual(match.external_url, "http://a.com")

    def test_choose_best_match_model(self):
        """Testa escolha de melhor match por modelo"""
        candidates = [
            {"title": "iPhone 14 Pro", "url": "http://a.com", "source": "zoom"},
            {"title": "iPhone 14 Pro Max", "url": "http://b.com", "source": "buscape"},
        ]

        target_title = "iPhone 14 Pro"

        match = self.matcher.choose_best_match(candidates, target_title)

        self.assertIsNotNone(match)
        self.assertEqual(match.match_type, "model")
        self.assertGreaterEqual(match.confidence, 0.95)

    def test_choose_best_match_title(self):
        """Testa escolha de melhor match por título"""
        candidates = [
            {
                "title": "Monitor LG 34 polegadas",
                "url": "http://a.com",
                "source": "zoom",
            },
            {
                "title": "Monitor Samsung 34 polegadas",
                "url": "http://b.com",
                "source": "buscape",
            },
        ]

        target_title = "Monitor LG 34 polegadas"

        match = self.matcher.choose_best_match(candidates, target_title)

        self.assertIsNotNone(match)
        # Pode ser model ou title, dependendo do que for extraído
        self.assertIn(match.match_type, ["model", "title"])
        self.assertGreaterEqual(match.confidence, 0.85)

    def test_choose_best_match_no_candidates(self):
        """Testa escolha quando não há candidatos"""
        candidates = []
        target_title = "iPhone 14 Pro"

        match = self.matcher.choose_best_match(candidates, target_title)
        self.assertIsNone(match)

    def test_choose_best_match_low_confidence(self):
        """Testa rejeição de candidatos com baixa confiança"""
        candidates = [
            {
                "title": "Produto Completamente Diferente",
                "url": "http://a.com",
                "source": "zoom",
            }
        ]

        target_title = "iPhone 14 Pro"

        match = self.matcher.choose_best_match(candidates, target_title)
        self.assertIsNone(match)

    def test_batch_match(self):
        """Testa matching em lote"""
        products = [
            {"title": "iPhone 14 Pro", "sku": "12345"},
            {"title": "Samsung Galaxy S22", "sku": "67890"},
        ]

        candidates = [
            {"title": "iPhone 14 Pro 256GB", "url": "http://a.com", "source": "zoom"},
            {
                "title": "Samsung Galaxy S22 Ultra",
                "url": "http://b.com",
                "source": "buscape",
            },
        ]

        matches = self.matcher.batch_match(products, candidates)

        # Pelo menos um match deve ser encontrado
        self.assertGreaterEqual(len(matches), 1)
        self.assertTrue(all(isinstance(match, ProductMatch) for match in matches))

    def test_validate_match(self):
        """Testa validação de matches"""
        # Teste match válido por EAN
        match = ProductMatch(
            external_url="http://test.com",
            confidence=1.0,
            match_type="ean",
            source="zoom",
        )
        self.assertTrue(self.matcher.validate_match(match, "Teste"))

        # Teste match válido por modelo
        match.confidence = 0.95
        match.match_type = "model"
        self.assertTrue(self.matcher.validate_match(match, "Teste"))

        # Teste match válido por título (categoria não restritiva)
        match.confidence = 0.87
        match.match_type = "title"
        self.assertTrue(self.matcher.validate_match(match, "iPhone 14 Pro"))

        # Teste match inválido por título (categoria restritiva)
        self.assertFalse(self.matcher.validate_match(match, "Cabo USB-C"))

        # Teste match com baixa confiança
        match.confidence = 0.8
        self.assertFalse(self.matcher.validate_match(match, "Teste"))


class TestMatcherFunctions(unittest.TestCase):
    """Testes para funções de conveniência"""

    def test_normalize_title_function(self):
        """Testa função normalize_title"""
        normalized = normalize_title("iPhone 14 Pro Max")
        self.assertIn("iphone", normalized)
        self.assertIn("14", normalized)
        self.assertIn("pro", normalized)
        self.assertIn("max", normalized)

    def test_extract_model_function(self):
        """Testa função extract_model"""
        model = extract_model("LG 34GP63A-B")
        self.assertEqual(model, "GP63A")

    def test_calculate_similarity_function(self):
        """Testa função calculate_similarity"""
        similarity = calculate_similarity("iPhone 14 Pro", "iPhone 14 Pro Max")
        self.assertGreater(similarity, 0.8)

    def test_choose_best_match_function(self):
        """Testa função choose_best_match"""
        candidates = [
            {"title": "iPhone 14 Pro", "url": "http://test.com", "source": "zoom"}
        ]

        match = choose_best_match(candidates, "iPhone 14 Pro")
        self.assertIsNotNone(match)
        self.assertEqual(match.external_url, "http://test.com")


if __name__ == "__main__":
    unittest.main()
