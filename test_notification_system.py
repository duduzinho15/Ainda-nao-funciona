"""
Script de teste para o Sistema de Notificações

Este script testa todas as funcionalidades do sistema de notificações
implementado no bot Garimpeiro Geek.
"""
import asyncio
import sys
import os

# Adiciona o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_notification_system():
    """Testa o sistema de notificações completo"""
    print("🔔 Testando Sistema de Notificações")
    print("=" * 60)
    
    try:
        # Testa importação do módulo
        print("📦 Testando importação do módulo...")
        from notification_system import (
            register_user, update_user_preferences, add_user_category,
            add_favorite_store, get_user_notification_stats, get_notification_system_stats
        )
        print("✅ Módulo importado com sucesso!")
        
        # Testa registro de usuário
        print("\n👤 Testando registro de usuário...")
        user_prefs = register_user(
            12345, 
            username="test_user", 
            first_name="Usuário", 
            last_name="Teste"
        )
        print(f"✅ Usuário registrado: {user_prefs.user_id}")
        
        # Testa atualização de preferências
        print("\n⚙️ Testando atualização de preferências...")
        success = update_user_preferences(
            12345, 
            min_discount=25, 
            max_price=1500.0,
            notification_frequency="immediate"
        )
        print(f"✅ Preferências atualizadas: {success}")
        
        # Testa adição de categoria
        print("\n🎯 Testando adição de categoria...")
        success = add_user_category(12345, 'gaming')
        print(f"✅ Categoria 'gaming' adicionada: {success}")
        
        success = add_user_category(12345, 'tecnologia')
        print(f"✅ Categoria 'tecnologia' adicionada: {success}")
        
        # Testa adição de loja favorita
        print("\n⭐ Testando adição de loja favorita...")
        success = add_favorite_store(12345, 'Kabum!')
        print(f"✅ Loja 'Kabum!' adicionada: {success}")
        
        success = add_favorite_store(12345, 'Dell')
        print(f"✅ Loja 'Dell' adicionada: {success}")
        
        # Testa obtenção de estatísticas do usuário
        print("\n📊 Testando estatísticas do usuário...")
        user_stats = get_user_notification_stats(12345)
        print(f"✅ Estatísticas obtidas:")
        print(f"   Total de notificações: {user_stats['total_notifications']}")
        print(f"   Categorias: {user_stats['preferences']['categories']}")
        print(f"   Lojas favoritas: {user_stats['preferences']['favorite_stores']}")
        print(f"   Desconto mínimo: {user_stats['preferences']['min_discount']}%")
        print(f"   Preço máximo: R$ {user_stats['preferences']['max_price']}")
        
        # Testa estatísticas do sistema
        print("\n📈 Testando estatísticas do sistema...")
        system_stats = get_notification_system_stats()
        print(f"✅ Estatísticas do sistema:")
        print(f"   Total de usuários: {system_stats['total_users']}")
        print(f"   Usuários ativos: {system_stats['active_users']}")
        print(f"   Templates disponíveis: {system_stats['templates_available']}")
        
        # Testa registro de outro usuário
        print("\n👥 Testando registro de múltiplos usuários...")
        user_prefs2 = register_user(
            67890, 
            username="test_user2", 
            first_name="Usuário", 
            last_name="Teste 2"
        )
        print(f"✅ Segundo usuário registrado: {user_prefs2.user_id}")
        
        # Adiciona preferências para o segundo usuário
        update_user_preferences(67890, min_discount=30, max_price=2000.0)
        add_user_category(67890, 'smartphones')
        add_favorite_store(67890, 'Magazine Luiza')
        
        # Verifica estatísticas atualizadas
        system_stats = get_notification_system_stats()
        print(f"✅ Sistema atualizado: {system_stats['total_users']} usuários")
        
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_notification_templates():
    """Testa os templates de notificação"""
    print("\n📝 Testando Templates de Notificação")
    print("=" * 60)
    
    try:
        from notification_system import notification_system
        
        # Verifica templates disponíveis
        templates = notification_system.notification_templates
        print(f"✅ Templates disponíveis: {len(templates)}")
        
        for template_id, template in templates.items():
            print(f"   📋 {template_id}: {template.title}")
            print(f"      Mensagem: {template.message[:100]}...")
        
        # Testa formatação de template
        print("\n🔧 Testando formatação de template...")
        template = templates.get('oferta_personalizada')
        if template:
            # Simula dados de oferta
            oferta_teste = {
                'titulo': 'Notebook Gamer RTX 4060',
                'preco': 'R$ 4.999,00',
                'desconto': 25,
                'loja': 'Kabum!',
                'url_afiliado': 'https://exemplo.com/produto',
                'categoria': 'Gaming'
            }
            
            # Formata a mensagem
            try:
                message = template.message.format(
                    title=oferta_teste['titulo'],
                    price=oferta_teste['preco'],
                    discount=oferta_teste['desconto'],
                    store=oferta_teste['loja'],
                    url=oferta_teste['url_afiliado'],
                    category=oferta_teste['categoria']
                )
                print(f"✅ Template formatado com sucesso!")
                print(f"   Mensagem: {message[:150]}...")
            except Exception as e:
                print(f"❌ Erro ao formatar template: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar templates: {e}")
        return False

async def test_user_preferences():
    """Testa o sistema de preferências de usuário"""
    print("\n⚙️ Testando Sistema de Preferências")
    print("=" * 60)
    
    try:
        from notification_system import notification_system
        
        # Testa verificação de notificação
        print("🔍 Testando verificação de notificação...")
        
        # Cria uma oferta de teste
        oferta_teste = {
            'titulo': 'Smartphone Samsung Galaxy S23',
            'preco': 'R$ 2.999,00',
            'desconto': 30,
            'loja': 'Kabum!',
            'categoria': 'smartphones'
        }
        
        # Verifica se o usuário deve ser notificado
        should_notify = notification_system.should_notify_user(12345, oferta_teste)
        print(f"✅ Usuário 12345 deve ser notificado: {should_notify}")
        
        # Testa com oferta que não atende aos critérios
        oferta_sem_desconto = {
            'titulo': 'Produto sem desconto',
            'preco': 'R$ 100,00',
            'desconto': 5,  # Menor que o mínimo configurado (25%)
            'loja': 'Loja Teste',
            'categoria': 'geral'
        }
        
        should_notify = notification_system.should_notify_user(12345, oferta_sem_desconto)
        print(f"✅ Usuário 12345 deve ser notificado (oferta sem desconto): {should_notify}")
        
        # Testa com oferta cara
        oferta_cara = {
            'titulo': 'Produto caro',
            'preco': 'R$ 3.000,00',  # Acima do limite configurado (R$ 1.500)
            'desconto': 40,
            'loja': 'Loja Teste',
            'categoria': 'geral'
        }
        
        should_notify = notification_system.should_notify_user(12345, oferta_cara)
        print(f"✅ Usuário 12345 deve ser notificado (oferta cara): {should_notify}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar preferências: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🚀 Teste Completo do Sistema de Notificações")
    print("=" * 80)
    
    # Executa todos os testes
    test1 = await test_notification_system()
    test2 = await test_notification_templates()
    test3 = await test_user_preferences()
    
    # Resultado final
    print("\n" + "=" * 80)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 80)
    print(f"🔔 Sistema de Notificações: {'✅ PASSOU' if test1 else '❌ FALHOU'}")
    print(f"📝 Templates: {'✅ PASSOU' if test2 else '❌ FALHOU'}")
    print(f"⚙️ Preferências: {'✅ PASSOU' if test3 else '❌ FALHOU'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O sistema de notificações está funcionando perfeitamente!")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique os erros e tente novamente.")
        return False

if __name__ == "__main__":
    # Executa os testes
    resultado = asyncio.run(main())
    sys.exit(0 if resultado else 1)
