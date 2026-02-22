"""
Tests for P7-B1 License Server (JWT + RBAC).
"""

import pytest
import sqlite3
import os
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from vjlive3.plugins.license_server import LicenseServer, License, ValidationResult
from vjlive3.plugins.api import PluginContext

# Test fixture config
TEST_DB_PATH = ":memory:"
TEST_SECRET = "super_secure_test_secret_key_12345"

@pytest.fixture
def license_server():
    """Provides a fresh, in-memory LicenseServer instance."""
    server = LicenseServer(secret_key=TEST_SECRET, db_path=TEST_DB_PATH)
    # Mock plugin context
    context = MagicMock(spec=PluginContext)
    context.get_parameter.return_value = None
    server.initialize(context)
    yield server
    server.cleanup()

def test_init_no_hardware():
    """Module starts without crashing and handles database connections."""
    server = LicenseServer(secret_key=TEST_SECRET, db_path=TEST_DB_PATH)
    assert server.name == "Unknown Plugin"  # From PluginBase unless overridden in class definition (we use METADATA)
    assert server.METADATA["name"] == "License Server"
    server.cleanup()
    
    # Initialize logic testing parameter inheritance
    server2 = LicenseServer(secret_key="", db_path="")
    ctx = MagicMock()
    ctx.get_parameter.side_effect = lambda param: "memory_db" if param == "db_path" else "my_secret"
    server2.initialize(ctx)
    assert server2._secret_key == "my_secret"
    assert server2._db_path == "memory_db"
    server2.cleanup()
    
def test_fallback_env_secret(monkeypatch):
    """Test fallback to environment variable structure"""
    monkeypatch.setenv("JWT_SECRET", "env_secret")
    server = LicenseServer()
    ctx = MagicMock()
    ctx.get_parameter.return_value = None
    server.initialize(ctx)
    assert server._secret_key == "env_secret"

def test_jwt_generation(license_server):
    """Generates valid JWTs."""
    payload = {"role": "admin", "custom": "data"}
    token = license_server.generate_jwt("user_123", payload)
    assert isinstance(token, str)
    assert len(token) > 20

def test_jwt_verification(license_server):
    """Verifies JWTs correctly."""
    payload = {"role": "admin", "custom": "data"}
    token = license_server.generate_jwt("user_123", payload)
    
    decoded = license_server.verify_jwt(token)
    assert decoded["sub"] == "user_123"
    assert decoded["role"] == "admin"
    assert decoded["custom"] == "data"
    assert "iat" in decoded

def test_jwt_verification_failures(license_server):
    """Handles errors gracefully (invalid / expired signatures)."""
    # 1. Invalid signature
    with pytest.raises(ValueError, match="Invalid token"):
        license_server.verify_jwt("invalid.token.string")
        
    # 2. Expired signature
    # We patch datetime inside the generate so it creates a token from the past
    past_time = datetime.now(timezone.utc) - timedelta(days=2)
    payload = {"exp": int(past_time.timestamp())}
    token = license_server.generate_jwt("user_123", payload)
    
    with pytest.raises(ValueError, match="Token has expired"):
        license_server.verify_jwt(token)

def test_no_secret_raises():
    """Fails if no secret key is set."""
    server = LicenseServer(secret_key="", db_path=":memory:")
    # We don't initialize it, so secret stays empty
    with pytest.raises(RuntimeError):
        server.generate_jwt("user", {})
    with pytest.raises(RuntimeError):
        server.verify_jwt("token")

def test_license_issuance(license_server):
    """Issues licenses correctly."""
    future = datetime.now(timezone.utc) + timedelta(days=30)
    lic = license_server.issue_license(
        user_id="user_john",
        plugin_id="p1_matrix",
        license_type="pro",
        expires_at=future
    )
    
    assert lic.user_id == "user_john"
    assert lic.plugin_id == "p1_matrix"
    assert lic.license_type == "pro"
    assert lic.revoked is False
    assert isinstance(lic.token, str)
    
    # Missing args
    with pytest.raises(ValueError):
        license_server.issue_license("", "plugin_1", "pro", future)

def test_license_validation(license_server):
    """Validates licenses correctly."""
    future = datetime.now(timezone.utc) + timedelta(days=30)
    lic = license_server.issue_license("user_x", "p1_matrix", "standard", future)
    
    # 1. Valid plugin match
    res = license_server.validate_license(lic.token, "p1_matrix")
    assert res.valid is True
    assert res.reason == "Valid"
    assert res.license_data["sub"] == "user_x"
    
    # 2. Invalid plugin mismatch
    res2 = license_server.validate_license(lic.token, "other_plugin")
    assert res2.valid is False
    assert "not other_plugin" in res2.reason
    
    # 3. Wildcard plugin match
    bundle_lic = license_server.issue_license("user_x", "*", "bundle", future)
    res3 = license_server.validate_license(bundle_lic.token, "anything")
    assert res3.valid is True

def test_license_revocation(license_server):
    """Revokes licenses correctly."""
    future = datetime.now(timezone.utc) + timedelta(days=30)
    lic = license_server.issue_license("user_rev", "p1_matrix", "standard", future)
    
    assert license_server.validate_license(lic.token, "p1_matrix").valid is True
    
    # Revoke
    assert license_server.revoke_license(lic.token) is True
    
    # Validate again
    res = license_server.validate_license(lic.token, "p1_matrix")
    assert res.valid is False
    assert "revoked" in res.reason
    
    # Unknown token
    assert license_server.revoke_license("unknown") is False

def test_get_licenses(license_server):
    """Can retrieve licenses by user or plugin."""
    future = datetime.now(timezone.utc) + timedelta(days=30)
    lic1 = license_server.issue_license("u1", "p1", "trial", future)
    lic2 = license_server.issue_license("u1", "p2", "pro", future)
    lic3 = license_server.issue_license("u2", "p1", "pro", future)
    
    u1_lics = license_server.get_user_licenses("u1")
    assert len(u1_lics) == 2
    
    p1_lics = license_server.get_plugin_licenses("p1")
    assert len(p1_lics) == 2

def test_rbac_permissions(license_server):
    """Role-based access control works."""
    # Create roles
    role1 = license_server.create_role("Admin", ["system:read", "system:write", "plugin:delete"])
    role2 = license_server.create_role("User", ["system:read"])
    role_wildcard = license_server.create_role("God", ["*"])
    
    assert role1 == "admin"
    assert role2 == "user"
    assert role_wildcard == "god"
    
    with pytest.raises(ValueError):
        license_server.create_role("", [])
    
    # Assign roles
    license_server.assign_role("alice", "admin")
    license_server.assign_role("bob", "user")
    license_server.assign_role("charlie", "god")
    
    with pytest.raises(ValueError):
        license_server.assign_role("", "admin")
        
    with pytest.raises(ValueError):
        license_server.assign_role("dave", "unknown_role")
        
    # Check permissions
    assert license_server.check_permission("alice", "plugin:delete") is True
    assert license_server.check_permission("alice", "unknown:perm") is False
    
    assert license_server.check_permission("bob", "system:read") is True
    assert license_server.check_permission("bob", "system:write") is False
    
    assert license_server.check_permission("charlie", "literally:anything") is True
    
    # Unknown user
    assert license_server.check_permission("nobody", "system:read") is False

def test_edge_cases_db_offline():
    """Handles errors gracefully when DB is offline but crypto checks pass."""
    server = LicenseServer(secret_key=TEST_SECRET, db_path=":memory:")
    # manually issue a token without initializing DB side
    expires = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {"type": "license", "plg": "plugin", "exp": int(expires.timestamp())}
    token = server.generate_jwt("user", payload)
    
    # DB is None
    server._conn = None
    res = server.validate_license(token, "plugin")
    
    # Should fallback to offline crypto pass
    assert res.valid is True
    assert "Offline" in res.reason

def test_db_initialization_error(monkeypatch):
    """Test what occurs if DB path is thoroughly invalid/permission denied"""
    server = LicenseServer(secret_key=TEST_SECRET, db_path="/root/invalid/db/path.db")
    ctx = MagicMock()
    ctx.get_parameter.return_value = None
    
    # SQLite will throw when trying to create a DB in a restricted folder
    server.initialize(ctx)
    assert server._conn is None

def test_invalid_json_permissions(license_server):
    """Handles corrupted json in database silently during RBAC check."""
    cursor = license_server._conn.cursor()
    cursor.execute("INSERT INTO roles (role_id, role_name, permissions) VALUES ('bad', 'Bad', 'not-json')")
    cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES ('u_bad', 'bad')")
    license_server._conn.commit()
    
    assert license_server.check_permission("u_bad", "any") is False
