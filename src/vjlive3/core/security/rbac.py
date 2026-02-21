"""Role-Based Access Control (RBAC) implementation.

This module provides:
- Role definitions with permission sets
- Permission decorators for API endpoints
- JWT-based role and permission extraction
- Access control enforcement
"""

import functools
import logging
from typing import Optional, Set, List, Dict, Any
from dataclasses import dataclass

from src.vjlive3.utils.security import validate_ip_address

logger = logging.getLogger(__name__)


# Role definitions
class Role:
    """Role constants with associated permissions."""
    
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'
    
    @staticmethod
    def get_permissions(role: str) -> Set[str]:
        """Get the set of permissions for a given role."""
        role_permissions = {
            Role.ADMIN: {
                'system:read',
                'system:write',
                'plugin:read',
                'plugin:write',
                'user:read',
                'user:write',
                'admin:read',
                'admin:write',
                'superadmin:access'
            },
            Role.USER: {
                'plugin:read',
                'plugin:write',  # Users can modify their own plugins
                'system:read',
                'user:read',
                'user:write'
            },
            Role.GUEST: {
                'plugin:read',
                'system:read'
            }
        }
        return role_permissions.get(role, set())
    
    @staticmethod
    def has_permission(role: str, required_permission: str) -> bool:
        """Check if a role has a specific permission."""
        permissions = Role.get_permissions(role)
        return required_permission in permissions
    
    @staticmethod
    def is_valid_role(role: str) -> bool:
        """Check if a role is valid."""
        return role in {Role.ADMIN, Role.USER, Role.GUEST}


@dataclass
class JWTPayload:
    """Parsed JWT payload with role and permissions."""
    user_id: Optional[str] = None
    role: str = Role.GUEST
    permissions: Set[str] = field(default_factory=set)
    exp: Optional[int] = None
    
    def has_permission(self, permission: str) -> bool:
        """Check if payload has a specific permission."""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if payload has a specific role."""
        return self.role == role
    
    def can(self, permission: str) -> bool:
        """Check if user can perform an action."""
        return self.has_permission(permission)


class RBACManager:
    """Manager for role-based access control."""
    
    def __init__(self):
        self.role_hierarchy = {
            Role.ADMIN: [Role.USER, Role.GUEST],
            Role.USER: [Role.GUEST]
        }
    
    def extract_jwt_payload(self, token: str) -> Optional[JWTPayload]:
        """Extract and validate JWT payload.
        
        In production, use a proper JWT library like PyJWT.
        This is a simplified implementation for demonstration.
        """
        try:
            # JWT format: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Invalid JWT format")
                return None
            
            # Decode payload (base64url)
            import base64
            import json
            
            payload = base64.urlsafe_b64decode(parts[1] + '==')
            claims = json.loads(payload)
            
            # Extract role and permissions
            role = claims.get('role', Role.GUEST)
            if not Role.is_valid_role(role):
                logger.warning(f"Invalid role in JWT: {role}")
                role = Role.GUEST
            
            # Get permissions from role and any explicit permissions
            permissions = set(Role.get_permissions(role))
            explicit_permissions = claims.get('permissions', [])
            permissions.update(explicit_permissions)
            
            return JWTPayload(
                user_id=claims.get('sub') or claims.get('user_id'),
                role=role,
                permissions=permissions,
                exp=claims.get('exp')
            )
        except (ValueError, json.JSONDecodeError, base64.binascii.Error) as e:
            logger.error(f"Failed to parse JWT: {e}")
            return None
    
    def check_access(self, payload: JWTPayload, required_permission: str = None, 
                     required_role: str = None) -> bool:
        """Check if user has access based on role/permissions."""
        if required_permission:
            if not payload.has_permission(required_permission):
                logger.debug(f"Access denied: missing permission {required_permission}")
                return False
        
        if required_role:
            if not payload.has_role(required_role):
                logger.debug(f"Access denied: missing role {required_role}")
                return False
        
        return True
    
    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from token."""
        payload = self.extract_jwt_payload(token)
        if not payload:
            return None
        
        return {
            'user_id': payload.user_id,
            'role': payload.role,
            'permissions': list(payload.permissions)
        }


# Global RBAC manager instance
rbac_manager = RBACManager()


def require_permission(permission: str):
    """Decorator to require a specific permission."""
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract token from request context
            # This assumes the function receives a request object or token
            token = _extract_token_from_args(args, kwargs)
            if not token:
                from flask import abort
                abort(401, description="Authentication required")
            
            payload = rbac_manager.extract_jwt_payload(token)
            if not payload:
                from flask import abort
                abort(401, description="Invalid token")
            
            if not rbac_manager.check_access(payload, required_permission=permission):
                from flask import abort
                abort(403, description=f"Missing required permission: {permission}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(role: str):
    """Decorator to require a specific role."""
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = _extract_token_from_args(args, kwargs)
            if not token:
                from flask import abort
                abort(401, description="Authentication required")
            
            payload = rbac_manager.extract_jwt_payload(token)
            if not payload:
                from flask import abort
                abort(401, description="Invalid token")
            
            if not rbac_manager.check_access(payload, required_role=role):
                from flask import abort
                abort(403, description=f"Missing required role: {role}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_admin():
    """Decorator to require admin role."""
    return require_role(Role.ADMIN)


def _extract_token_from_args(args, kwargs) -> Optional[str]:
    """Extract JWT token from function arguments.
    
    This tries to find the token in common locations:
    - kwargs['token']
    - kwargs['request'].headers.get('Authorization')
    - args that look like request objects
    """
    # Check kwargs first
    if 'token' in kwargs:
        token = kwargs['token']
        if isinstance(token, str):
            return token
    
    if 'request' in kwargs:
        request = kwargs['request']
        auth_header = getattr(request, 'headers', {}).get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
    
    # Check args for request-like objects
    for arg in args:
        if hasattr(arg, 'headers') and hasattr(arg, 'args'):
            auth_header = arg.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                return auth_header[7:]
    
    return None


def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    """Get current user information from token."""
    return rbac_manager.get_user_info(token)


def has_permission(token: str, permission: str) -> bool:
    """Check if a token has a specific permission."""
    payload = rbac_manager.extract_jwt_payload(token)
    if not payload:
        return False
    return payload.has_permission(permission)


def has_role(token: str, role: str) -> bool:
    """Check if a token has a specific role."""
    payload = rbac_manager.extract_jwt_payload(token)
    if not payload:
        return False
    return payload.has_role(role)


# Convenience functions for testing

def create_test_token(user_id: str, role: str = Role.USER, 
                     permissions: List[str] = None, exp: int = None) -> str:
    """Create a test JWT token (for testing only)."""
    import base64
    import json
    import time
    
    # Create payload
    payload = {
        'sub': user_id,
        'user_id': user_id,
        'role': role,
        'iat': int(time.time())
    }
    
    if permissions:
        payload['permissions'] = permissions
    
    if exp:
        payload['exp'] = exp
    else:
        # Token valid for 1 hour
        payload['exp'] = int(time.time()) + 3600
    
    # Encode payload
    payload_bytes = json.dumps(payload).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b'=').decode('utf-8')
    
    # Create a simple token (header.payload.signature)
    # In production, sign with proper secret
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_bytes = json.dumps(header).encode('utf-8')
    header_b64 = base64.urlsafe_b64encode(header_bytes).rstrip(b'=').decode('utf-8')
    
    # For testing, use a simple signature
    signature_b64 = base64.urlsafe_b64encode(b'test_signature').rstrip(b'=').decode('utf-8')
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def get_all_permissions() -> Set[str]:
    """Get all available permissions."""
    all_perms = set()
    for role in [Role.ADMIN, Role.USER, Role.GUEST]:
        all_perms.update(Role.get_permissions(role))
    return all_perms


def get_roles_with_permission(permission: str) -> List[str]:
    """Get all roles that have a specific permission."""
    roles = []
    for role in [Role.ADMIN, Role.USER, Role.GUEST]:
        if Role.has_permission(role, permission):
            roles.append(role)
    return roles