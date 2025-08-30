#!/usr/bin/env python3
"""
Teste de validação de formato de todos os conversores de afiliados
Verificar se todos os conversores seguem os padrões corretos
"""

import importlib
import os
import sys

# Adicionar src e tests ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, os.path.dirname(__file__))

from tests.data.affiliate_examples import (
    ALIEXPRESS,
    AMAZON,
    AWIN,
    MAGALU,
    MERCADO_LIVRE,
    SHOPEE,
)


def test_validacao_formato_conversores():
    """Testa formato de todos os conversores de afiliados"""
    print("🧪 TESTANDO FORMATO DE TODOS OS CONVERSORES DE AFILIADOS")
    print("=" * 80)

    # Definir conversores e suas funções de validação
    conversores = {
        "awin": {
            "module": "src.affiliate.awin",
            "validator": "validate_awin_deeplink",
            "examples": [
                AWIN["comfy_home"]["deeplink"],
                AWIN["comfy_product"]["deeplink"],
                AWIN["trocafy_home"]["deeplink"],
                AWIN["lg_home"]["deeplink"],
                AWIN["kabum_home"]["deeplink"],
            ],
        },
        "amazon": {
            "module": "src.affiliate.amazon",
            "validator": "is_valid_amazon_url",
            "examples": [
                AMAZON["canon_1"],
                AMAZON["canon_2"],
                "https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR",
            ],
        },
        "mercadolivre": {
            "module": "src.affiliate.mercadolivre",
            "validator": "validate_ml_url",
            "examples": [
                MERCADO_LIVRE["short_1"],
                MERCADO_LIVRE["short_2"],
                MERCADO_LIVRE["short_3"],
            ],
        },
        "shopee": {
            "module": "src.affiliate.shopee",
            "validator": "validate_shopee_url",
            "examples": [
                SHOPEE["short_1"],
                SHOPEE["short_2"],
                SHOPEE["short_3"],
            ],
        },
        "magazineluiza": {
            "module": "src.affiliate.magazineluiza",
            "validator": "validate_magazine_url",
            "examples": [
                MAGALU["vitrine_1"],
                MAGALU["vitrine_2"],
            ],
        },
        "aliexpress": {
            "module": "src.affiliate.aliexpress",
            "validator": "validate_aliexpress_url",
            "examples": [
                ALIEXPRESS["short_1"],
                ALIEXPRESS["short_2"],
                ALIEXPRESS["short_3"],
                ALIEXPRESS["short_4"],
                ALIEXPRESS["short_5"],
            ],
        },
    }

    # Teste do validador centralizado
    print("\n🔍 TESTANDO VALIDADOR CENTRALIZADO:")
    try:
        from src.utils.affiliate_validator import (
            get_validation_summary,
            validate_affiliate_link,
        )

        summary = get_validation_summary()
        print("   ✅ Validador centralizado carregado")
        print(f"   📊 Plataformas suportadas: {len(summary['platforms'])}")
        print(f"   📋 Plataformas: {', '.join(summary['platforms'])}")

        # Testar algumas URLs com o validador centralizado
        test_urls = [
            (
                "https://www.awin1.com/cread.php?awinmid=23377&awinaffid=2370719&ued=https%3A%2F%2Fwww.comfy.com.br%2F",
                "awin",
            ),
            ("https://mercadolivre.com/sec/1vt6gtj", "mercadolivre"),
            ("https://s.shopee.com.br/3LGfnEjEXu", "shopee"),
            (
                "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/",
                "magazineluiza",
            ),
            (
                "https://www.amazon.com.br/dp/B09T4WC9GN?tag=garimpeirogee-20&language=pt_BR",
                "amazon",
            ),
            ("https://s.click.aliexpress.com/e/_opftn1L", "aliexpress"),
        ]

        centralized_success = 0
        for url, expected_platform in test_urls:
            is_valid, platform, error = validate_affiliate_link(url, expected_platform)
            if is_valid:
                print(f"   ✅ {expected_platform.upper()}: Válido")
                centralized_success += 1
            else:
                print(f"   ❌ {expected_platform.upper()}: {error}")

        print(
            f"   📈 Taxa de sucesso centralizada: {centralized_success}/{len(test_urls)} ({centralized_success/len(test_urls)*100:.1f}%)"
        )

    except ImportError as e:
        print(f"   ❌ Erro ao carregar validador centralizado: {e}")

    # Resultados por conversor
    results = {}
    total_success = 0
    total_tests = 0

    print("\n🔧 TESTANDO CONVERSORES INDIVIDUAIS:")

    for conversor_name, config in conversores.items():
        print(f"\n📋 {conversor_name.upper()}:")

        try:
            # Importar módulo dinamicamente
            module = importlib.import_module(config["module"])
            validator_func = getattr(module, config["validator"])

            print(f"   ✅ Módulo carregado: {config['module']}")
            print(f"   ✅ Função validadora: {config['validator']}")

            # Testar exemplos
            success_count = 0
            for i, url in enumerate(config["examples"], 1):
                print(f"\n   {i}. 🔍 {url[:60]}...")

                try:
                    # Diferentes assinaturas de função
                    if conversor_name == "amazon":
                        # Amazon tem função diferente
                        is_valid = validator_func(url)
                        error = "Formato inválido" if not is_valid else ""
                    else:
                        # Outros retornam tupla (is_valid, error)
                        result = validator_func(url)
                        if isinstance(result, tuple):
                            is_valid, error = result
                        else:
                            is_valid = result
                            error = "Formato inválido" if not is_valid else ""

                    if is_valid:
                        print("      ✅ VÁLIDO")
                        success_count += 1
                        total_success += 1
                    else:
                        print(f"      ❌ INVÁLIDO: {error}")

                    total_tests += 1

                except Exception as e:
                    print(f"      💥 ERRO: {e}")
                    total_tests += 1

            success_rate = (
                (success_count / len(config["examples"]) * 100)
                if config["examples"]
                else 0
            )
            print(
                f"\n   📊 Taxa de sucesso: {success_count}/{len(config['examples'])} ({success_rate:.1f}%)"
            )

            results[conversor_name] = {
                "success": success_count,
                "total": len(config["examples"]),
                "rate": success_rate,
                "status": "OK" if success_rate >= 90 else "FALHA",
            }

        except ImportError as e:
            print(f"   ❌ Erro ao importar módulo: {e}")
            results[conversor_name] = {
                "success": 0,
                "total": len(config["examples"]),
                "rate": 0,
                "status": "ERRO_IMPORT",
            }
        except AttributeError as e:
            print(f"   ❌ Função validadora não encontrada: {e}")
            results[conversor_name] = {
                "success": 0,
                "total": len(config["examples"]),
                "rate": 0,
                "status": "ERRO_FUNCAO",
            }
        except Exception as e:
            print(f"   ❌ Erro inesperado: {e}")
            results[conversor_name] = {
                "success": 0,
                "total": len(config["examples"]),
                "rate": 0,
                "status": "ERRO_GERAL",
            }

    # Teste de consistência entre conversores
    print("\n🔄 TESTANDO CONSISTÊNCIA ENTRE CONVERSORES:")

    consistency_tests = [
        # Teste: URL inválida deve ser rejeitada por todos
        ("https://exemplo-invalido.com/produto", "URL inválida"),
        # Teste: URL de outra plataforma deve ser rejeitada
        ("https://www.google.com/search?q=produto", "URL de busca Google"),
    ]

    for invalid_url, description in consistency_tests:
        print(f"\n   🔍 {description}: {invalid_url}")
        consistent_rejections = 0

        for conversor_name, config in conversores.items():
            try:
                module = importlib.import_module(config["module"])
                validator_func = getattr(module, config["validator"])

                if conversor_name == "amazon":
                    is_valid = validator_func(invalid_url)
                else:
                    result = validator_func(invalid_url)
                    is_valid = result[0] if isinstance(result, tuple) else result

                if not is_valid:
                    consistent_rejections += 1
                    print(f"      ✅ {conversor_name.upper()}: Rejeitado corretamente")
                else:
                    print(f"      ❌ {conversor_name.upper()}: Aceitou incorretamente")

            except Exception as e:
                print(f"      ⚠️ {conversor_name.upper()}: Erro ao testar - {e}")

        consistency_rate = consistent_rejections / len(conversores) * 100
        print(
            f"   📊 Consistência: {consistent_rejections}/{len(conversores)} ({consistency_rate:.1f}%)"
        )

    # Resumo final
    print("\n🎯 RESUMO FINAL:")
    print("   📊 RESULTADOS POR CONVERSOR:")

    for conversor_name, result in results.items():
        status_emoji = "✅" if result["status"] == "OK" else "❌"
        print(
            f"      {status_emoji} {conversor_name.upper()}: {result['success']}/{result['total']} ({result['rate']:.1f}%) - {result['status']}"
        )

    overall_success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    print(
        f"\n   📈 TAXA GERAL DE SUCESSO: {overall_success_rate:.1f}% ({total_success}/{total_tests})"
    )

    # Verificar arquivos essenciais
    print("\n📁 VERIFICANDO ARQUIVOS ESSENCIAIS:")
    essential_files = [
        "src/affiliate/__init__.py",
        "src/affiliate/base_api.py",
        "src/utils/affiliate_validator.py",
        "src/posting/posting_manager.py",
        "tests/data/affiliate_examples.py",
    ]

    missing_files = []
    for file_path in essential_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - AUSENTE")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n   ⚠️ ARQUIVOS AUSENTES: {len(missing_files)}")
    else:
        print("\n   ✅ TODOS OS ARQUIVOS ESSENCIAIS PRESENTES")

    # Critério de sucesso
    success_criteria = (
        overall_success_rate >= 85.0  # 85% de URLs válidas aceitas
        and len(missing_files) == 0  # Todos arquivos essenciais presentes
        and len([r for r in results.values() if r["status"] == "OK"])
        >= 4  # Pelo menos 4 conversores funcionando
    )

    if success_criteria:
        print("\n   🎉 VALIDAÇÃO DE FORMATO APROVADA!")
        return True
    else:
        print("\n   ⚠️ VALIDAÇÃO DE FORMATO REPROVADA!")
        return False


if __name__ == "__main__":
    try:
        success = test_validacao_formato_conversores()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 ERRO: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
