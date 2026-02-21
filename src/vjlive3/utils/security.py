"""Security utilities for VJLive3.

This module provides security-related helper functions for input validation,
path sanitization, and safe operations.
"""

import os
import re
from pathlib import Path
from typing import Optional, Set


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize a filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename (may be unsafe)
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename safe for use

    Example:
        >>> safe = sanitize_filename("../../../etc/passwd")
        >>> print(safe)  # "passwd" or similar
    """
    # Remove directory components
    filename = os.path.basename(filename)

    # Remove any remaining path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove control characters
    filename = "".join(c for c in filename if ord(c) >= 32)

    # Remove dangerous patterns
    dangerous_patterns = [
        r"\.\.",
        r"[:;]",
        r"[<>\"*?|]",
        r"\0",
    ]
    for pattern in dangerous_patterns:
        filename = re.sub(pattern, "_", filename)

    # Limit length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    # Ensure not empty
    if not filename:
        filename = "unnamed"

    return filename


def validate_path(
    path: Path,
    base_dir: Optional[Path] = None,
    allow_absolute: bool = False,
) -> bool:
    """Validate that a path is safe and within allowed boundaries.

    Args:
        path: Path to validate
        base_dir: Optional base directory that path must be within
        allow_absolute: If True, allow absolute paths (still validated)

    Returns:
        True if path is safe, False otherwise

    Example:
        >>> safe = validate_path(Path("data/config.yaml"), base_dir=Path("config/"))
    """
    try:
        # Resolve to absolute path
        if path.is_absolute():
            if not allow_absolute:
                return False
            resolved = path.resolve()
        else:
            # Relative path - resolve against current directory
            resolved = path.resolve()

        # Check for suspicious patterns
        if ".." in path.parts:
            return False

        # If base_dir specified, ensure path is within it
        if base_dir:
            base_resolved = base_dir.resolve()
            try:
                resolved.relative_to(base_resolved)
            except ValueError:
                return False

        # Check that path doesn't point to special files
        if resolved.exists():
            stat = resolved.stat()
            # Check if it's a regular file or directory
            if not stat.st_mode & 0o100000:  # S_IFREG
                return False

        return True

    except (OSError, ValueError):
        return False


def is_safe_join(base_dir: Path, user_path: str) -> bool:
    """Check if joining base_dir with user_path is safe.

    Args:
        base_dir: Base directory
        user_path: User-provided path component

    Returns:
        True if safe, False otherwise
    """
    # Resolve both paths
    try:
        base_resolved = base_dir.resolve()
        full_path = (base_resolved / user_path).resolve()
    except OSError:
        return False

    # Check that the result is within base_dir
    try:
        full_path.relative_to(base_resolved)
    except ValueError:
        return False

    return True


def validate_port(port: int) -> bool:
    """Validate that a port number is in valid range.

    Args:
        port: Port number to validate

    Returns:
        True if valid, False otherwise
    """
    return 1 <= port <= 65535


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format.

    Args:
        ip: IP address string (IPv4 or IPv6)

    Returns:
        True if valid, False otherwise
    """
    import socket

    try:
        # Try IPv4
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        try:
            # Try IPv6
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False


def check_for_secrets(content: str) -> List[str]:
    """Check if content contains potential secrets.

    Args:
        content: Text content to scan

    Returns:
        List of potential secret patterns found
    """
    # Common secret patterns
    patterns = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"[0-9a-zA-Z/+]{40}",
        "GitHub Token": r"ghp_[0-9a-zA-Z]{36}",
        "Generic API Key": r"['\"][0-9a-zA-Z]{32,}['\"]",
        "Password in URL": r"[a-zA-Z]+://[^:]+:[^@]+@",
        "Private Key": r"-----BEGIN (RSA )?PRIVATE KEY-----",
    }

    findings = []
    for name, pattern in patterns.items():
        if re.search(pattern, content):
            findings.append(name)

    return findings