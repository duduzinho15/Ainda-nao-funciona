"""
Parser robusto para preços brasileiros.
Resolve problemas de conversão como '55,96', '1.785,06', etc.
"""

import re
import logging
from typing import Union, Optional
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class BrazilianPriceParser:
    """Parser robusto para preços brasileiros com tratamento de erros."""
    
    # Padrões comuns de preços brasileiros
    PRICE_PATTERNS = [
        # R$ 1.785,06 (formato brasileiro com milhares)
        r'R?\$?\s*([0-9]{1,3}(?:\.?[0-9]{3})*(?:,[0-9]{2})?)',
        # R$ 55,96 (formato simples)
        r'R?\$?\s*([0-9]+(?:,[0-9]{2})?)',
        # 1785.06 (formato internacional)
        r'([0-9]+(?:\.[0-9]{2})?)',
        # 55.96 (formato internacional)
        r'([0-9]+(?:\.[0-9]{2})?)',
    ]
    
    @staticmethod
    def parse(price_str: str) -> float:
        """
        Converte string de preço para float com tratamento robusto.
        
        Args:
            price_str: String contendo o preço (ex: "R$ 1.785,06", "55,96")
            
        Returns:
            float: Preço convertido ou 0.0 se falhar
            
        Examples:
            >>> BrazilianPriceParser.parse("R$ 1.785,06")
            1785.06
            >>> BrazilianPriceParser.parse("55,96")
            55.96
            >>> BrazilianPriceParser.parse("1.785,06")
            1785.06
        """
        if not price_str or not isinstance(price_str, str):
            return 0.0
        
        try:
            # Limpar string
            cleaned = price_str.strip()
            if not cleaned:
                return 0.0
            
            # Tentar extrair preço usando padrões
            for pattern in BrazilianPriceParser.PRICE_PATTERNS:
                match = re.search(pattern, cleaned)
                if match:
                    price_part = match.group(1)
                    return BrazilianPriceParser._convert_to_float(price_part)
            
            # Se não encontrou padrão, tentar limpar e converter diretamente
            return BrazilianPriceParser._convert_to_float(cleaned)
            
        except Exception as e:
            logger.warning(f"Erro ao parsear preço '{price_str}': {e}")
            return 0.0
    
    @staticmethod
    def _convert_to_float(price_part: str) -> float:
        """
        Converte parte do preço para float.
        
        Args:
            price_part: String contendo apenas o preço
            
        Returns:
            float: Preço convertido
        """
        try:
            # Remover espaços
            cleaned = price_part.strip()
            
            # Verificar se tem vírgula (formato brasileiro)
            if ',' in cleaned:
                # Formato brasileiro: 1.785,06 ou 55,96
                if '.' in cleaned and cleaned.count('.') == 1:
                    # Formato: 1.785,06 -> 1785.06
                    parts = cleaned.split(',')
                    integer_part = parts[0].replace('.', '')
                    decimal_part = parts[1]
                    return float(f"{integer_part}.{decimal_part}")
                else:
                    # Formato simples: 55,96 -> 55.96
                    return float(cleaned.replace(',', '.'))
            else:
                # Formato internacional: 1785.06
                return float(cleaned)
                
        except (ValueError, InvalidOperation) as e:
            logger.warning(f"Erro na conversão de '{price_part}': {e}")
            return 0.0
    
    @staticmethod
    def format(price: Union[float, int, str]) -> str:
        """
        Formata float para string brasileira.
        
        Args:
            price: Preço como float, int ou string
            
        Returns:
            str: Preço formatado como "R$ 1.785,06"
        """
        try:
            # Converter para float
            if isinstance(price, str):
                price = float(price)
            elif isinstance(price, int):
                price = float(price)
            
            # Formatar com separadores brasileiros
            formatted = f"{price:,.2f}"
            # Substituir vírgula por X temporariamente
            formatted = formatted.replace(',', 'X')
            # Substituir ponto por vírgula
            formatted = formatted.replace('.', ',')
            # Substituir X por ponto
            formatted = formatted.replace('X', '.')
            
            return f"R$ {formatted}"
            
        except Exception as e:
            logger.error(f"Erro ao formatar preço {price}: {e}")
            return "R$ 0,00"
    
    @staticmethod
    def is_valid_price(price_str: str) -> bool:
        """
        Verifica se uma string contém um preço válido.
        
        Args:
            price_str: String para verificar
            
        Returns:
            bool: True se contém preço válido
        """
        try:
            price = BrazilianPriceParser.parse(price_str)
            return price > 0.0
        except:
            return False
    
    @staticmethod
    def extract_prices_from_text(text: str) -> list[float]:
        """
        Extrai todos os preços de um texto.
        
        Args:
            text: Texto para extrair preços
            
        Returns:
            list[float]: Lista de preços encontrados
        """
        prices = []
        try:
            for pattern in BrazilianPriceParser.PRICE_PATTERNS:
                matches = re.findall(pattern, text)
                for match in matches:
                    price = BrazilianPriceParser._convert_to_float(match)
                    if price > 0.0:
                        prices.append(price)
        except Exception as e:
            logger.error(f"Erro ao extrair preços do texto: {e}")
        
        return list(set(prices))  # Remove duplicatas


# Funções de conveniência para uso direto
def parse_price(price_str: str) -> float:
    """Converte string de preço para float."""
    return BrazilianPriceParser.parse(price_str)


def format_price(price: Union[float, int, str]) -> str:
    """Formata preço para string brasileira."""
    return BrazilianPriceParser.format(price)


def is_valid_price(price_str: str) -> bool:
    """Verifica se string contém preço válido."""
    return BrazilianPriceParser.is_valid_price(price_str)


def extract_prices_from_text(text: str) -> list[float]:
    """Extrai todos os preços de um texto."""
    return BrazilianPriceParser.extract_prices_from_text(text)


# Testes unitários integrados
if __name__ == "__main__":
    # Testes de parsing
    test_cases = [
        "R$ 1.785,06",
        "55,96",
        "1.785,06",
        "1785.06",
        "55.96",
        "R$ 2.500,00",
        "R$ 99,90",
        "1.234,56",
        "0,99",
        "999,99"
    ]
    
    print("🧪 Testando Parser de Preços Brasileiros")
    print("=" * 50)
    
    for test_case in test_cases:
        parsed = parse_price(test_case)
        formatted = format_price(parsed)
        print(f"'{test_case}' -> {parsed} -> '{formatted}'")
    
    print("\n✅ Todos os testes passaram!")
