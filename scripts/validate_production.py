import sys
import json
from pathlib import Path

def validate():
    print("Running Production Configuration Validation...")
    errors = []
    
    # Check docker-compose
    dc_path = Path("docker-compose.prod.yml")
    if not dc_path.exists():
        errors.append("docker-compose.prod.yml is missing")
    else:
        content = dc_path.read_text()
        if "restart: unless-stopped" not in content:
            errors.append("docker-compose missing restart policy")
        if "limits:" not in content:
            errors.append("docker-compose missing resource limits")
            
    # Check Dockerfile
    df_path = Path("Dockerfile.production")
    if not df_path.exists():
        errors.append("Dockerfile.production is missing")
    else:
        content = df_path.read_text()
        if "USER vjlive" not in content:
            errors.append("Dockerfile does not drop root privileges")
            
    # Generate output
    report = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors
    }
    
    out_path = Path("validation_report.json")
    out_path.write_text(json.dumps(report, indent=2))
    
    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f" - {e}")
        return 1
    else:
        print("Validation PASSED")
        return 0

if __name__ == '__main__':
    sys.exit(validate())
