#!/usr/bin/env python3
"""
Configurações do Sistema de Notificações
"""

# Configurações de Notificações
NOTIFICATION_SETTINGS = {
    # Intervalos de verificação
    "check_interval_minutes": 30,  # Verifica a cada 30 minutos
    "daily_deals_interval_hours": 2,  # Ofertas do dia a cada 2 horas
    "price_drops_interval_hours": 1,  # Quedas de preço a cada hora
    "admin_status_interval_hours": 6,  # Status para admin a cada 6 horas
    
    # Horários específicos
    "daily_summary_time": "20:00",  # Resumo diário às 20:00
    "morning_alert_time": "09:00",  # Alerta matinal às 9:00
    "evening_alert_time": "18:00",  # Alerta vespertino às 18:00
    
    # Configurações de ofertas
    "max_offers_per_notification": 3,  # Máximo de ofertas por notificação
    "min_commission_rate": 5.0,  # Taxa de comissão mínima para notificar
    "min_discount_threshold": 20.0,  # Desconto mínimo para notificar
    "high_commission_threshold": 8.0,  # Comissão alta para alertas especiais
    
    # Configurações de preço
    "price_ranges": [
        {"min": 10, "max": 50, "title": "💰 **OFERTAS ATÉ R$ 50** 💰"},
        {"min": 50, "max": 100, "title": "💰 **OFERTAS R$ 50 - R$ 100** 💰"},
        {"min": 100, "max": 200, "title": "💰 **OFERTAS R$ 100 - R$ 200** 💰"},
        {"min": 200, "max": 500, "title": "💰 **OFERTAS R$ 200 - R$ 500** 💰"},
        {"min": 500, "max": 1000, "title": "💰 **OFERTAS R$ 500+** 💰"}
    ],
    
    # Configurações de histórico
    "max_sent_offers_history": 100,  # Máximo de ofertas no histórico
    "clear_history_daily": True,  # Limpa histórico diariamente
    
    # Configurações de spam
    "min_delay_between_notifications": 2,  # Delay mínimo entre notificações (segundos)
    "max_notifications_per_hour": 10,  # Máximo de notificações por hora
    
    # Configurações de categorias
    "categories_to_monitor": [
        "eletronicos",
        "informatica", 
        "games",
        "casa",
        "moda",
        "esportes"
    ],
    
    # Configurações de palavras-chave
    "keywords_to_monitor": [
        "smartphone",
        "notebook",
        "headphone",
        "mouse",
        "teclado",
        "monitor",
        "placa de video",
        "processador"
    ]
}

# Configurações de Mensagens
MESSAGE_TEMPLATES = {
    "best_offers": {
        "title": "🔥 **ALERTA DE OFERTAS EXCEPCIONAIS!** 🔥",
        "message": "Encontramos ofertas com comissões muito altas! Aproveite agora:"
    },
    
    "daily_deals": {
        "title": "⭐ **OFERTAS DO DIA - SHOPEE** ⭐",
        "message": "Novas ofertas imperdíveis foram encontradas:"
    },
    
    "price_drops": {
        "title": "📉 **ALERTA DE QUEDA DE PREÇO** 📉",
        "message": "Produtos com desconto significativo:"
    },
    
    "daily_summary": {
        "title": "📊 **RESUMO DIÁRIO - SHOPEE** 📊",
        "message": "📈 **Estatísticas do dia:**"
    },
    
    "admin_status": {
        "title": "🤖 **STATUS DO SISTEMA DE NOTIFICAÇÕES**",
        "message": "✅ Sistema funcionando normalmente"
    },
    
    "morning_alert": {
        "title": "🌅 **BOM DIA! OFERTAS DA MANHÃ** 🌅",
        "message": "Comece o dia com as melhores ofertas:"
    },
    
    "evening_alert": {
        "title": "🌆 **BOA TARDE! OFERTAS DA TARDE** 🌆",
        "message": "Aproveite as ofertas do final do dia:"
    }
}

# Configurações de Filtros
FILTER_SETTINGS = {
    "commission_filters": {
        "low": {"min": 0.1, "max": 2.0, "priority": 1},
        "medium": {"min": 2.0, "max": 5.0, "priority": 2},
        "high": {"min": 5.0, "max": 10.0, "priority": 3},
        "exceptional": {"min": 10.0, "max": 100.0, "priority": 4}
    },
    
    "price_filters": {
        "budget": {"min": 0, "max": 50, "priority": 1},
        "affordable": {"min": 50, "max": 200, "priority": 2},
        "premium": {"min": 200, "max": 1000, "priority": 3},
        "luxury": {"min": 1000, "max": 10000, "priority": 4}
    },
    
    "rating_filters": {
        "minimum_rating": 4.0,
        "preferred_rating": 4.5,
        "excellent_rating": 4.8
    }
}

# Configurações de Prioridade
PRIORITY_SETTINGS = {
    "high_priority_conditions": [
        "commission_rate >= 15.0",
        "commission_rate >= 10.0 AND price <= 100",
        "commission_rate >= 8.0 AND price <= 50"
    ],
    
    "medium_priority_conditions": [
        "commission_rate >= 8.0",
        "commission_rate >= 5.0 AND price <= 200"
    ],
    
    "low_priority_conditions": [
        "commission_rate >= 3.0",
        "price <= 100"
    ]
}

# Configurações de Horários de Pico
PEAK_TIME_SETTINGS = {
    "morning_peak": {
        "start": "08:00",
        "end": "10:00",
        "multiplier": 1.5  # Aumenta frequência de notificações
    },
    
    "lunch_peak": {
        "start": "12:00", 
        "end": "14:00",
        "multiplier": 1.2
    },
    
    "evening_peak": {
        "start": "18:00",
        "end": "20:00", 
        "multiplier": 1.8
    },
    
    "night_quiet": {
        "start": "23:00",
        "end": "07:00",
        "multiplier": 0.3  # Reduz frequência à noite
    }
}

# Configurações de Teste
TEST_SETTINGS = {
    "enable_test_mode": False,
    "test_chat_id": None,  # ID do chat para testes
    "test_interval_seconds": 60,  # Intervalo para testes
    "max_test_notifications": 5  # Máximo de notificações de teste
}

# Configurações de Log
LOG_SETTINGS = {
    "log_level": "INFO",
    "log_file": "notifications.log",
    "max_log_size_mb": 10,
    "backup_count": 5,
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# Configurações de Performance
PERFORMANCE_SETTINGS = {
    "max_concurrent_requests": 5,
    "request_timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 5,
    "cache_duration_minutes": 15
}

# Configurações de Backup
BACKUP_SETTINGS = {
    "enable_backup": True,
    "backup_interval_hours": 24,
    "max_backup_files": 7,
    "backup_directory": "backups/notifications"
}

# Função para obter configurações
def get_notification_config():
    """Retorna todas as configurações de notificação"""
    return {
        "notification": NOTIFICATION_SETTINGS,
        "messages": MESSAGE_TEMPLATES,
        "filters": FILTER_SETTINGS,
        "priority": PRIORITY_SETTINGS,
        "peak_times": PEAK_TIME_SETTINGS,
        "test": TEST_SETTINGS,
        "log": LOG_SETTINGS,
        "performance": PERFORMANCE_SETTINGS,
        "backup": BACKUP_SETTINGS
    }

# Função para obter configuração específica
def get_config_section(section_name: str):
    """Retorna uma seção específica de configuração"""
    configs = get_notification_config()
    return configs.get(section_name, {})

# Função para validar configurações
def validate_config():
    """Valida se todas as configurações estão corretas"""
    errors = []
    
    # Valida intervalos
    if NOTIFICATION_SETTINGS["check_interval_minutes"] < 1:
        errors.append("Intervalo de verificação deve ser >= 1 minuto")
    
    if NOTIFICATION_SETTINGS["max_offers_per_notification"] < 1:
        errors.append("Máximo de ofertas deve ser >= 1")
    
    if NOTIFICATION_SETTINGS["min_commission_rate"] < 0:
        errors.append("Taxa de comissão mínima deve ser >= 0")
    
    # Valida horários
    try:
        from datetime import datetime
        datetime.strptime(NOTIFICATION_SETTINGS["daily_summary_time"], "%H:%M")
        datetime.strptime(NOTIFICATION_SETTINGS["morning_alert_time"], "%H:%M")
        datetime.strptime(NOTIFICATION_SETTINGS["evening_alert_time"], "%H:%M")
    except ValueError:
        errors.append("Formato de horário inválido (use HH:MM)")
    
    return errors

if __name__ == "__main__":
    # Testa as configurações
    print("🔧 TESTANDO CONFIGURAÇÕES DE NOTIFICAÇÃO")
    print("=" * 50)
    
    errors = validate_config()
    
    if errors:
        print("❌ Erros encontrados:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Todas as configurações estão válidas!")
        
        # Mostra algumas configurações
        print(f"\n📋 Configurações principais:")
        print(f"   🔍 Verificação a cada: {NOTIFICATION_SETTINGS['check_interval_minutes']} minutos")
        print(f"   💰 Desconto mínimo: {NOTIFICATION_SETTINGS['min_discount_threshold']}%")
        print(f"   💸 Comissão mínima: {NOTIFICATION_SETTINGS['min_commission_rate']}%")
        print(f"   📊 Máximo por notificação: {NOTIFICATION_SETTINGS['max_offers_per_notification']}")
        print(f"   ⏰ Resumo diário: {NOTIFICATION_SETTINGS['daily_summary_time']}")
