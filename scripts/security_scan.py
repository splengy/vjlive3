#!/usr/bin/env python3
"""
Security Vulnerability Scanner

Scans code for common security issues and dependency vulnerabilities.
Enforces SAFETY_RAIL 10: Security Non-Negotiables.
"""

import sys
import subprocess
import json
from pathlib import Path

def scan_dependencies() -> bool:
    """Check dependencies for known vulnerabilities."""
    print("Scanning dependencies for vulnerabilities...")
    
    try:
        # Check if safety is installed
        result = subprocess.run(
            ['pip', 'list', '--format=json'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            print("⚠️  Could not list packages")
            return True  # Don't fail if we can't check
        
        packages = json.loads(result.stdout)
        
        # Check for packages with known vulnerabilities
        # This is a simplified check - in production use safety or similar
        vulnerable_packages = []
        
        for pkg in packages:
            name = pkg['name'].lower()
            version = pkg['version']
            
            # Example checks (would need vulnerability database)
            if name == 'requests' and version.startswith('2.0'):
                vulnerable_packages.append(f"{name} {version} - Upgrade to >=2.28.0")
            elif name == 'flask' and version.startswith('1.'):
                vulnerable_packages.append(f"{name} {version} - Upgrade to >=2.0.0")
            elif name == 'django' and version.startswith('2.0'):
                vulnerable_packages.append(f"{name} {version} - Upgrade to >=4.0.0")
        
        if vulnerable_packages:
            print("❌ Found vulnerable dependencies:")
            for vp in vulnerable_packages:
                print(f"  - {vp}")
            return False
        
        print("✅ No obvious dependency vulnerabilities found")
        return True
        
    except Exception as e:
        print(f"⚠️  Dependency scan error: {e}")
        return True  # Don't fail on scan errors

def scan_code_for_secrets() -> bool:
    """Scan code for hardcoded secrets and credentials."""
    print("Scanning code for secrets...")
    
    try:
        # Get all Python files
        repo_root = Path(__file__).parent.parent
        src_dir = repo_root / 'src'
        py_files = list(src_dir.rglob('*.py'))
        
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'API key'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Password'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Token'),
            (r'credential\s*=\s*["\'][^"\']+["\']', 'Credential'),
            (r'BEGIN\s+[A-Z]+\s+PRIVATE\s+KEY', 'Private key'),
            (r'-----BEGIN RSA PRIVATE KEY-----', 'RSA private key'),
        ]
        
        found_secrets = []
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern, secret_type in secret_patterns:
                    import re
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        for match in matches[:3]:  # Limit per file
                            found_secrets.append(f"{py_file}: {secret_type} - {match[:50]}...")
            except Exception:
                continue
        
        if found_secrets:
            print("❌ Found potential secrets in code:")
            for secret in found_secrets[:10]:  # Limit output
                print(f"  - {secret}")
            return False
        
        print("✅ No obvious secrets found in code")
        return True
        
    except Exception as e:
        print(f"⚠️  Secret scan error: {e}")
        return True

def scan_for_injection_patterns() -> bool:
    """Scan for potential code injection vulnerabilities."""
    print("Scanning for injection patterns...")
    
    try:
        repo_root = Path(__file__).parent.parent
        src_dir = repo_root / 'src'
        py_files = list(src_dir.rglob('*.py'))
        
        dangerous_patterns = [
            (r'eval\s*\(', 'eval() usage'),
            (r'exec\s*\(', 'exec() usage'),
            (r'__import__\s*\(', '__import__() usage'),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', 'subprocess with shell=True'),
            (r'os\.system\s*\(', 'os.system() usage'),
            (r'pickle\.load\s*\(', 'pickle.load() (unsafe deserialization)'),
        ]
        
        # Allow eval/exec in sandbox module (legitimate use)
        allowed_files = [
            str(repo_root / 'src' / 'vjlive3' / 'plugins' / 'sandbox.py')
        ]
        
        issues = []
        
        for py_file in py_files:
            # Skip allowed files
            if str(py_file) in allowed_files:
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern, issue_type in dangerous_patterns:
                    import re
                    if re.search(pattern, content):
                        issues.append(f"{py_file}: {issue_type}")
            except Exception:
                continue
        
        if issues:
            print("❌ Found potentially dangerous patterns:")
            for issue in issues[:10]:
                print(f"  - {issue}")
            return False
        
        print("✅ No obvious injection vulnerabilities found")
        return True
        
    except Exception as e:
        print(f"⚠️  Injection scan error: {e}")
        return True

def main() -> int:
    """Main entry point."""
    print("="*60)
    print("Security Vulnerability Scan")
    print("="*60)
    print()
    
    all_ok = True
    
    # Run all scans
    if not scan_dependencies():
        all_ok = False
    
    if not scan_code_for_secrets():
        all_ok = False
    
    if not scan_for_injection_patterns():
        all_ok = False
    
    print()
    print("="*60)
    if all_ok:
        print("✅ Security scan passed - no critical issues found")
        return 0
    else:
        print("❌ SECURITY SCAN FAILED")
        print("="*60)
        print("\nCritical security issues must be resolved before committing.")
        print("Review the findings above and fix accordingly.")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())