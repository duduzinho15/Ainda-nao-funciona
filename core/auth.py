"""
Sistema de autenticação JWT para o Garimpeiro Geek.
Suporta roles, rate limiting e segurança avançada.
"""

import os
import jwt
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Roles de usuário no sistema."""
    GUEST = "guest"           # Usuário não autenticado
    USER = "user"             # Usuário básico
    PREMIUM = "premium"       # Usuário premium
    SCRAPER = "scraper"       # Sistema de scraping
    ADMIN = "admin"           # Administrador
    SYSTEM = "system"         # Sistema interno


@dataclass
class UserClaims:
    """Claims do usuário no JWT."""
    user_id: int
    telegram_id: int
    username: str
    role: UserRole
    permissions: list[str]
    created_at: datetime
    expires_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'user_id': self.user_id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'role': self.role.value,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }


class AuthManager:
    """Gerenciador principal de autenticação."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or self._get_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # Cache de tokens revogados
        self.revoked_tokens = set()
        
        # Rate limiting por usuário
        self.rate_limit_store = {}
        self.max_requests_per_minute = 60
        
        logger.info("✅ Sistema de autenticação inicializado")
    
    def _get_secret_key(self) -> str:
        """Obtém chave secreta do ambiente ou gera uma nova."""
        secret_key = os.getenv("JWT_SECRET_KEY")
        if secret_key:
            return secret_key
        
        # Gerar chave secreta se não existir
        secret_key = secrets.token_urlsafe(32)
        
        # Salvar em arquivo de configuração
        config_dir = Path(".data/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / "auth.json"
        config_data = {
            "jwt_secret_key": secret_key,
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info("🔑 Nova chave JWT gerada e salva")
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível salvar chave JWT: {e}")
        
        return secret_key
    
    def create_access_token(self, user_data: Dict[str, Any], 
                          expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria JWT token de acesso.
        
        Args:
            user_data: Dados do usuário
            expires_delta: Tempo de expiração personalizado
            
        Returns:
            str: JWT token
        """
        try:
            # Configurar expiração
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Criar claims
            claims = UserClaims(
                user_id=user_data.get('id'),
                telegram_id=user_data.get('telegram_id'),
                username=user_data.get('username', ''),
                role=UserRole(user_data.get('role', 'user')),
                permissions=user_data.get('permissions', []),
                created_at=datetime.utcnow(),
                expires_at=expire
            )
            
            # Criar payload
            payload = {
                "sub": str(user_data.get('id')),
                "exp": expire,
                "iat": datetime.utcnow(),
                "claims": claims.to_dict()
            }
            
            # Gerar token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"✅ Token criado para usuário {user_data.get('username')}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar token: {e}")
            raise
    
    def create_refresh_token(self, user_id: int) -> str:
        """
        Cria JWT token de refresh.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            str: JWT refresh token
        """
        try:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            payload = {
                "sub": str(user_id),
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh"
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"✅ Refresh token criado para usuário {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar refresh token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[UserClaims]:
        """
        Verifica e decodifica JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            UserClaims ou None se inválido
        """
        try:
            # Verificar se token foi revogado
            if token in self.revoked_tokens:
                logger.warning("⚠️ Token revogado")
                return None
            
            # Decodificar token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verificar expiração
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.warning("⚠️ Token expirado")
                return None
            
            # Extrair claims
            claims_data = payload.get('claims', {})
            if not claims_data:
                logger.warning("⚠️ Token sem claims válidos")
                return None
            
            # Criar objeto UserClaims
            claims = UserClaims(
                user_id=claims_data.get('user_id'),
                telegram_id=claims_data.get('telegram_id'),
                username=claims_data.get('username', ''),
                role=UserRole(claims_data.get('role', 'user')),
                permissions=claims_data.get('permissions', []),
                created_at=datetime.fromisoformat(claims_data.get('created_at')),
                expires_at=datetime.fromisoformat(claims_data.get('expires_at'))
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Token inválido: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao verificar token: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoga um token JWT.
        
        Args:
            token: Token para revogar
            
        Returns:
            bool: True se revogado com sucesso
        """
        try:
            self.revoked_tokens.add(token)
            
            # Limpar tokens antigos (manter apenas últimos 1000)
            if len(self.revoked_tokens) > 1000:
                self.revoked_tokens = set(list(self.revoked_tokens)[-1000:])
            
            logger.info("✅ Token revogado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao revogar token: {e}")
            return False
    
    def check_rate_limit(self, user_id: int) -> bool:
        """
        Verifica rate limiting para um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            bool: True se dentro do limite
        """
        try:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            
            # Limpar registros antigos
            if user_id in self.rate_limit_store:
                self.rate_limit_store[user_id] = [
                    timestamp for timestamp in self.rate_limit_store[user_id]
                    if timestamp > minute_ago
                ]
            else:
                self.rate_limit_store[user_id] = []
            
            # Verificar limite
            if len(self.rate_limit_store[user_id]) >= self.max_requests_per_minute:
                logger.warning(f"⚠️ Rate limit excedido para usuário {user_id}")
                return False
            
            # Adicionar timestamp atual
            self.rate_limit_store[user_id].append(now)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar rate limit: {e}")
            return True  # Permitir em caso de erro
    
    def has_permission(self, claims: UserClaims, permission: str) -> bool:
        """
        Verifica se usuário tem permissão específica.
        
        Args:
            claims: Claims do usuário
            permission: Permissão para verificar
            
        Returns:
            bool: True se tem permissão
        """
        try:
            # Admin tem todas as permissões
            if claims.role == UserRole.ADMIN:
                return True
            
            # System tem todas as permissões
            if claims.role == UserRole.SYSTEM:
                return True
            
            # Verificar permissão específica
            return permission in claims.permissions
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar permissão: {e}")
            return False
    
    def require_auth(self, min_role: UserRole = UserRole.USER):
        """
        Decorator para requerer autenticação.
        
        Args:
            min_role: Role mínimo necessário
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Verificar token no primeiro argumento ou kwargs
                token = None
                if args and isinstance(args[0], str):
                    token = args[0]
                elif 'token' in kwargs:
                    token = kwargs['token']
                
                if not token:
                    raise ValueError("Token não fornecido")
                
                # Verificar token
                claims = self.verify_token(token)
                if not claims:
                    raise ValueError("Token inválido ou expirado")
                
                # Verificar role mínimo
                if claims.role.value < min_role.value:
                    raise ValueError(f"Role insuficiente. Necessário: {min_role.value}")
                
                # Verificar rate limiting
                if not self.check_rate_limit(claims.user_id):
                    raise ValueError("Rate limit excedido")
                
                # Adicionar claims aos kwargs
                kwargs['user_claims'] = claims
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_permission(self, permission: str):
        """
        Decorator para requerer permissão específica.
        
        Args:
            permission: Permissão necessária
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Verificar claims
                claims = kwargs.get('user_claims')
                if not claims:
                    raise ValueError("Claims do usuário não encontrados")
                
                # Verificar permissão
                if not self.has_permission(claims, permission):
                    raise ValueError(f"Permissão insuficiente: {permission}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Instância global
auth_manager = AuthManager()

# Funções de conveniência
def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Cria token de acesso."""
    return auth_manager.create_access_token(user_data, expires_delta)

def verify_token(token: str) -> Optional[UserClaims]:
    """Verifica token."""
    return auth_manager.verify_token(token)

def require_auth(min_role: UserRole = UserRole.USER):
    """Decorator para autenticação."""
    return auth_manager.require_auth(min_role)

def require_permission(permission: str):
    """Decorator para permissão."""
    return auth_manager.require_permission(permission)


# Exemplo de uso
if __name__ == "__main__":
    print("🧪 Testando Sistema de Autenticação")
    print("=" * 50)
    
    # Dados de teste
    test_user = {
        'id': 1,
        'telegram_id': 123456789,
        'username': 'testuser',
        'role': 'user',
        'permissions': ['read_offers', 'create_reviews']
    }
    
    # Criar token
    try:
        token = create_access_token(test_user)
        print(f"✅ Token criado: {token[:50]}...")
        
        # Verificar token
        claims = verify_token(token)
        if claims:
            print(f"✅ Token verificado para usuário: {claims.username}")
            print(f"   Role: {claims.role.value}")
            print(f"   Permissões: {claims.permissions}")
        else:
            print("❌ Falha na verificação do token")
        
        # Testar rate limiting
        if auth_manager.check_rate_limit(1):
            print("✅ Rate limit OK")
        else:
            print("❌ Rate limit excedido")
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
    
    print("\n✅ Teste de autenticação concluído!")
