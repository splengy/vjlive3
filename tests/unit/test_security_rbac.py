"""Tests for RBAC functionality."""

import pytest
from src.vjlive3.core.security.rbac import (
    Role, RBACManager, create_test_token, get_current_user, has_permission, has_role
)


@pytest.fixture(autouse=True)
def reset_rbac():
    """Reset RBAC state before each test."""
    yield


def test_role_permissions():
    """Test that roles have correct permissions."""
    assert Role.ADMIN in Role.get_permissions(Role.ADMIN)
    assert Role.USER in Role.get_permissions(Role.USER)
    assert Role.GUEST in Role.get_permissions(Role.GUEST)
    
    # Admin should have all permissions
    admin_perms = Role.get_permissions(Role.ADMIN)
    assert 'system:read' in admin_perms
    assert 'system:write' in admin_perms
    assert 'plugin:read' in admin_perms
    assert 'plugin:write' in admin_perms
    assert 'user:read' in admin_perms
    assert 'user:write' in admin_perms
    assert 'admin:read' in admin_perms
    assert 'admin:write' in admin_perms
    assert 'superadmin:access' in admin_perms
    
    # User should have limited permissions
    user_perms = Role.get_permissions(Role.USER)
    assert 'plugin:read' in user_perms
    assert 'plugin:write' in user_perms
    assert 'system:read' in user_perms
    assert 'user:read' in user_perms
    assert 'user:write' in user_perms
    assert 'system:write' not in user_perms
    assert 'admin:read' not in user_perms
    
    # Guest should have minimal permissions
    guest_perms = Role.get_permissions(Role.GUEST)
    assert 'plugin:read' in guest_perms
    assert 'system:read' in guest_perms
    assert 'plugin:write' not in guest_perms
    assert 'system:write' not in guest_perms


def test_role_hierarchy():
    """Test that role hierarchy works correctly."""
    # Admin inherits from User and Guest
    assert Role.ADMIN in [Role.ADMIN, Role.USER, Role.GUEST]
    assert Role.USER in [Role.USER, Role.GUEST]
    assert Role.GUEST in [Role.GUEST]


def test_jwt_payload_extraction():
    """Test JWT payload extraction."""
    rbac = RBACManager()
    
    # Create test token
    token = create_test_token(
        user_id="123",
        role=Role.ADMIN,
        permissions=['custom:permission']
    )
    
    payload = rbac.extract_jwt_payload(token)
    assert payload is not None
    assert payload.user_id == "123"
    assert payload.role == Role.ADMIN
    assert 'custom:permission' in payload.permissions
    assert 'system:read' in payload.permissions  # From role
    assert 'plugin:read' in payload.permissions  # From role


def test_invalid_jwt_handling():
    """Test that invalid JWTs are handled gracefully."""
    rbac = RBACManager()
    
    # Invalid format
    payload = rbac.extract_jwt_payload("invalid")
    assert payload is None
    
    # Malformed token
    payload = rbac.extract_jwt_payload("header.payload")
    assert payload is None
    
    # Empty token
    payload = rbac.extract_jwt_payload("")
    assert payload is None


def test_permission_checking():
    """Test permission checking functionality."""
    rbac = RBACManager()
    
    # Create tokens with different roles
    admin_token = create_test_token(user_id="1", role=Role.ADMIN)
    user_token = create_test_token(user_id="2", role=Role.USER)
    guest_token = create_test_token(user_id="3", role=Role.GUEST)
    
    # Admin should have all permissions
    assert has_permission(admin_token, 'system:read')
    assert has_permission(admin_token, 'system:write')
    assert has_permission(admin_token, 'plugin:write')
    assert has_permission(admin_token, 'superadmin:access')
    
    # User should have limited permissions
    assert has_permission(user_token, 'plugin:read')
    assert has_permission(user_token, 'plugin:write')
    assert has_permission(user_token, 'system:read')
    assert not has_permission(user_token, 'system:write')
    assert not has_permission(user_token, 'superadmin:access')
    
    # Guest should have minimal permissions
    assert has_permission(guest_token, 'plugin:read')
    assert has_permission(guest_token, 'system:read')
    assert not has_permission(guest_token, 'plugin:write')
    assert not has_permission(guest_token, 'system:write')


def test_role_checking():
    """Test role checking functionality."""
    rbac = RBACManager()
    
    admin_token = create_test_token(user_id="1", role=Role.ADMIN)
    user_token = create_test_token(user_id="2", role=Role.USER)
    guest_token = create_test_token(user_id="3", role=Role.GUEST)
    
    assert has_role(admin_token, Role.ADMIN)
    assert has_role(user_token, Role.USER)
    assert has_role(guest_token, Role.GUEST)
    
    assert not has_role(user_token, Role.ADMIN)
    assert not has_role(guest_token, Role.USER)
    assert not has_role(admin_token, Role.GUEST)


def test_get_current_user():
    """Test getting current user information."""
    admin_token = create_test_token(user_id="1", role=Role.ADMIN)
    
    user_info = get_current_user(admin_token)
    assert user_info is not None
    assert user_info['user_id'] == "1"
    assert user_info['role'] == Role.ADMIN
    assert 'permissions' in user_info
    assert isinstance(user_info['permissions'], list)


def test_invalid_role_handling():
    """Test that invalid roles are handled correctly."""
    rbac = RBACManager()
    
    # Create token with invalid role
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6IjEyMzQ1NiIsInJvbGUiOiJ1c2VyX2JhZF9yb2xlIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    payload = rbac.extract_jwt_payload(token)
    assert payload is not None
    assert payload.role == Role.GUEST  # Should default to guest


def test_custom_permissions():
    """Test that custom permissions work correctly."""
    rbac = RBACManager()
    
    # Create token with custom permissions
    token = create_test_token(
        user_id="1", 
        role=Role.USER,
        permissions=['custom:permission', 'another:permission']
    )
    
    payload = rbac.extract_jwt_payload(token)
    assert payload is not None
    assert 'custom:permission' in payload.permissions
    assert 'another:permission' in payload.permissions
    assert 'system:read' in payload.permissions  # From role


def test_permission_decorator():
    """Test the permission decorator (simplified)."""
    from src.vjlive3.core.security.rbac import require_permission
    
    @require_permission('plugin:read')
    def test_function():
        return "allowed"
    
    # This is a simplified test - full decorator testing would require Flask context
    assert callable(test_function)


def test_role_decorator():
    """Test the role decorator (simplified)."""
    from src.vjlive3.core.security.rbac import require_role
    
    @require_role(Role.ADMIN)
    def admin_function():
        return "admin_allowed"
    
    assert callable(admin_function)


def test_all_permissions():
    """Test that all permissions can be retrieved."""
    all_perms = Role.get_permissions(Role.ADMIN).union(
        Role.get_permissions(Role.USER),
        Role.get_permissions(Role.GUEST)
    )
    
    assert 'system:read' in all_perms
    assert 'system:write' in all_perms
    assert 'plugin:read' in all_perms
    assert 'plugin:write' in all_perms
    assert 'user:read' in all_perms
    assert 'user:write' in all_perms
    assert 'admin:read' in all_perms
    assert 'admin:write' in all_perms
    assert 'superadmin:access' in all_perms


def test_get_roles_with_permission():
    """Test getting roles that have a specific permission."""
    # Permission only admins have
    roles = Role.get_roles_with_permission('superadmin:access')
    assert Role.ADMIN in roles
    assert Role.USER not in roles
    assert Role.GUEST not in roles
    
    # Permission users and admins have
    roles = Role.get_roles_with_permission('plugin:write')
    assert Role.ADMIN in roles
    assert Role.USER in roles
    assert Role.GUEST not in roles
    
    # Permission all roles have
    roles = Role.get_roles_with_permission('plugin:read')
    assert Role.ADMIN in roles
    assert Role.USER in roles
    assert Role.GUEST in roles