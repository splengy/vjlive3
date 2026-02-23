"""
P7-B1: License Server (JWT + RBAC)

Centralized license management and role-based access control (RBAC).
Provides JWT-based authentication and SQLite-backed license validation.
"""

import logging
import sqlite3
import weakref
import os
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
import jwt


_logger = logging.getLogger("vjlive3.plugins.license_server")


@dataclass
class License:
    """Represents a granted software license."""
    token: str
    user_id: str
    plugin_id: str
    license_type: str
    expires_at: datetime
    issued_at: datetime
    revoked: bool = False


@dataclass
class ValidationResult:
    """Result of validating a license token."""
    valid: bool
    reason: str
    license_data: Optional[Dict[str, Any]] = None


class LicenseServer(object):
    """
    License and RBAC Management Server.
    Complies with P7-B1 specifications for offline/online JWT validation
    and explicit RBAC database.
    """
    
    METADATA = {
        "name": "License Server",
        "description": "Provides secure JWT licensing and Role-Based Access Control.",
        "version": "1.0.0",
        "author": "VJLive Team",
        "category": "core.business",
        "parameters": [
            {"name": "secret_key", "type": "string", "default": ""},
            {"name": "db_path", "type": "string", "default": "licenses.db"}
        ],
        "inputs": [],
        "outputs": []
    }

    def __init__(self, secret_key: str = "", db_path: str = "licenses.db") -> None:
        super().__init__()
        # In actual plugin environment, these might be overridden by context
        self._secret_key = secret_key
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def initialize(self, context) -> None:
        """Initialize the plugin context and database connection."""
        super().initialize(context)
        
        # Read from parameters if not provided in constructor
        if not self._secret_key:
            self._secret_key = self.context.get_parameter("secret_key") or os.getenv("JWT_SECRET", "default_insecure_secret_for_tests")
        
        param_db_path = self.context.get_parameter("db_path")
        if param_db_path:
            self._db_path = param_db_path
            
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema."""
        try:
            # Connect to sqlite (can be memory or file)
            self._conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Use dictionary-like cursor
            self._conn.row_factory = sqlite3.Row
            
            cursor = self._conn.cursor()
            
            # Licenses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                plugin_id TEXT NOT NULL,
                license_type TEXT NOT NULL,
                issued_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked BOOLEAN NOT NULL DEFAULT 0
            )
            ''')
            
            # Roles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY,
                role_name TEXT NOT NULL,
                permissions TEXT NOT NULL
            )
            ''')
            
            # User roles mapping
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (role_id) REFERENCES roles (role_id)
            )
            ''')
            
            self._conn.commit()
            _logger.info("License Server database initialized at %s", self._db_path)
            
        except sqlite3.Error as e:
            _logger.error("Failed to initialize database: %s", e)
            if self._conn:
                self._conn.close()
                self._conn = None

    def cleanup(self) -> None:
        """Close DB connections and free resources."""
        _logger.debug("Cleaning up License Server")
        if self._conn:
            try:
                self._conn.close()
            except Exception as e:
                _logger.warning("Error closing database connection: %s", e)
            self._conn = None
        super().cleanup()

    # ─── JWT Core ────────────────────────────────────────────────────────────

    def generate_jwt(self, user_id: str, payload: Dict[str, Any]) -> str:
        """Generate a signed JWT token."""
        if not self._secret_key:
            raise RuntimeError("JWT secret key not configured")
            
        token_payload = {
            "sub": user_id,
            "iat": datetime.now(timezone.utc),
            **payload
        }
        
        return jwt.encode(token_payload, self._secret_key, algorithm="HS256")

    def verify_jwt(self, token: str) -> Dict[str, Any]:
        """Verify a JWT token and return its payload."""
        if not self._secret_key:
            raise RuntimeError("JWT secret key not configured")
            
        try:
            return jwt.decode(token, self._secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

    # ─── Licensing ───────────────────────────────────────────────────────────

    def issue_license(self, user_id: str, plugin_id: str, license_type: str, expires_at: datetime) -> License:
        """Issue a new license and store it in the database."""
        if not user_id or not plugin_id:
            raise ValueError("User ID and Plugin ID are required")
            
        if self._conn is None:
            self._init_db()
            
        issued_at = datetime.now(timezone.utc)
        
        # Ensure UTC timezone for expires_at if naive
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        payload = {
            "type": "license",
            "plg": plugin_id,
            "lic_type": license_type,
            "exp": int(expires_at.timestamp())
        }
        
        token = self.generate_jwt(user_id, payload)
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO licenses (token, user_id, plugin_id, license_type, issued_at, expires_at, revoked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (token, user_id, plugin_id, license_type, issued_at, expires_at, False)
            )
            self._conn.commit()
            
            return License(
                token=token,
                user_id=user_id,
                plugin_id=plugin_id,
                license_type=license_type,
                expires_at=expires_at,
                issued_at=issued_at,
                revoked=False
            )
        except sqlite3.Error as e:
            _logger.error("Database error issuing license: %s", e)
            raise RuntimeError(f"Failed to issue license: {e}")

    def validate_license(self, license_token: str, plugin_id: str) -> ValidationResult:
        """Validate a license token cryptographically and database-wise."""
        try:
            # 1. Cryptographic validation (handles signature and basic expiration via 'exp' claim)
            payload = self.verify_jwt(license_token)
        except ValueError as e:
            return ValidationResult(valid=False, reason=str(e))
            
        # 2. Check plugin match
        token_plugin_id = payload.get("plg")
        if token_plugin_id != plugin_id and token_plugin_id != "*":  # allow wildcard for bundle licenses
            return ValidationResult(valid=False, reason=f"License is for plugin {token_plugin_id}, not {plugin_id}")
            
        # 3. Database validation (revocation check)
        if self._conn is None:
            # If we're truly offline and have no access to the DB at all,
            # we must fallback to the cryptographic check alone to fulfill OFFLINE-FIRST rail.
            _logger.warning("Validating license via cryptography only (DB unavailable)")
            return ValidationResult(valid=True, reason="Valid (Offline Mode)", license_data=payload)
            
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT revoked FROM licenses WHERE token = ?", (license_token,))
            row = cursor.fetchone()
            
            if row is None:
                # License is valid cryptographically but doesn't exist in our DB.
                # Could be a legit offline license generated by the root server.
                # OFFLINE-FIRST: Allow it if signature passed.
                return ValidationResult(valid=True, reason="Valid (Remote License)", license_data=payload)
                
            if row['revoked']:
                return ValidationResult(valid=False, reason="License has been revoked")
                
            return ValidationResult(valid=True, reason="Valid", license_data=payload)
            
        except sqlite3.Error as e:
            _logger.error("DB Error during validation: %s", e)
            # Fallback to offline validation
            return ValidationResult(valid=True, reason="Valid (Offline Fallback)", license_data=payload)

    def revoke_license(self, license_token: str) -> bool:
        """Revoke a license in the database."""
        if self._conn is None:
            self._init_db()
            
        try:
            cursor = self._conn.cursor()
            cursor.execute("UPDATE licenses SET revoked = 1 WHERE token = ?", (license_token,))
            
            if cursor.rowcount == 0:
                return False  # License not found
                
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            _logger.error("Database error revoking license: %s", e)
            return False

    def get_user_licenses(self, user_id: str) -> List[License]:
        """Get all licenses associated with a user."""
        if self._conn is None:
            self._init_db()
            
        licenses = []
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM licenses WHERE user_id = ?", (user_id,))
            
            for row in cursor.fetchall():
                licenses.append(License(
                    token=row['token'],
                    user_id=row['user_id'],
                    plugin_id=row['plugin_id'],
                    license_type=row['license_type'],
                    issued_at=row['issued_at'],
                    expires_at=row['expires_at'],
                    revoked=bool(row['revoked'])
                ))
        except sqlite3.Error as e:
            _logger.error("Database error fetching user licenses: %s", e)
            
        return licenses

    def get_plugin_licenses(self, plugin_id: str) -> List[License]:
        """Get all licenses associated with a specific plugin."""
        if self._conn is None:
            self._init_db()
            
        licenses = []
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM licenses WHERE plugin_id = ?", (plugin_id,))
            
            for row in cursor.fetchall():
                licenses.append(License(
                    token=row['token'],
                    user_id=row['user_id'],
                    plugin_id=row['plugin_id'],
                    license_type=row['license_type'],
                    issued_at=row['issued_at'],
                    expires_at=row['expires_at'],
                    revoked=bool(row['revoked'])
                ))
        except sqlite3.Error as e:
            _logger.error("Database error fetching plugin licenses: %s", e)
            
        return licenses

    # ─── RBAC (Role-Based Access Control) ────────────────────────────────────

    def create_role(self, role_name: str, permissions: List[str]) -> str:
        """Create a new role with the given permissions."""
        if not role_name:
            raise ValueError("Role name cannot be empty")
            
        if self._conn is None:
            self._init_db()
            
        role_id = role_name.lower().replace(" ", "_")
        perms_json = json.dumps(permissions)
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO roles (role_id, role_name, permissions) VALUES (?, ?, ?)",
                (role_id, role_name, perms_json)
            )
            self._conn.commit()
            return role_id
        except sqlite3.Error as e:
            _logger.error("Database error creating role: %s", e)
            raise RuntimeError(f"Failed to create role: {e}")

    def assign_role(self, user_id: str, role_id: str) -> None:
        """Assign a role to a user."""
        if not user_id or not role_id:
            raise ValueError("User ID and Role ID cannot be empty")
            
        if self._conn is None:
            self._init_db()
            
        try:
            cursor = self._conn.cursor()
            # Verify role exists
            cursor.execute("SELECT 1 FROM roles WHERE role_id = ?", (role_id,))
            if not cursor.fetchone():
                raise ValueError(f"Role {role_id} does not exist")
                
            cursor.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id)
            )
            self._conn.commit()
        except sqlite3.Error as e:
            _logger.error("Database error assigning role: %s", e)
            raise RuntimeError(f"Failed to assign role: {e}")

    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission via their roles."""
        if self._conn is None:
            self._init_db()
            
        try:
            cursor = self._conn.cursor()
            # Get all roles for user
            cursor.execute("""
                SELECT r.permissions 
                FROM roles r
                JOIN user_roles ur ON r.role_id = ur.role_id
                WHERE ur.user_id = ?
            """, (user_id,))
            
            for row in cursor.fetchall():
                try:
                    perms = json.loads(row['permissions'])
                    if permission in perms or "*" in perms:
                        return True
                except json.JSONDecodeError:
                    continue
                    
            return False
        except sqlite3.Error as e:
            _logger.error("Database error checking permission: %s", e)
            # Default deny on error
            return False
