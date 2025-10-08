#!/usr/bin/env python3
"""
Render Configuration Validator for TG-Fets Trading Bot
Validates all configuration files for Render deployment
"""

import os
import json
import sys

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[0;34m",
        "SUCCESS": "\033[0;32m",
        "WARNING": "\033[1;33m",
        "ERROR": "\033[0;31m"
    }
    reset = "\033[0m"
    try:
        print(f"{colors.get(status, '')}[{status}]{reset} {message}")
    except UnicodeEncodeError:
        print(f"[{status}] {message}")

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print_status(f"[OK] {description} found: {file_path}", "SUCCESS")
        return True
    else:
        print_status(f"[MISSING] {description} not found: {file_path}", "ERROR")
        return False

def validate_yaml(file_path, description):
    """Validate YAML file"""
    try:
        import yaml
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        print_status(f"[OK] {description} is valid YAML", "SUCCESS")
        return True
    except ImportError:
        print_status(f"[WARNING] PyYAML not installed, skipping YAML validation", "WARNING")
        return True
    except Exception as e:
        print_status(f"[ERROR] {description} has invalid YAML: {e}", "ERROR")
        return False
    except FileNotFoundError:
        print_status(f"[MISSING] {description} not found: {file_path}", "ERROR")
        return False

def validate_dockerfile(file_path):
    """Validate Dockerfile for Render"""
    if not os.path.exists(file_path):
        print_status(f"[MISSING] Dockerfile not found: {file_path}", "ERROR")
        return False
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    issues = []
    
    # Check for required elements
    if "FROM python:" not in content:
        issues.append("Missing Python base image")
    
    if "EXPOSE 8080" not in content:
        issues.append("Missing port 8080 exposure")
    
    if "HEALTHCHECK" not in content:
        issues.append("Missing health check")
    
    if "USER botuser" not in content:
        issues.append("Missing non-root user setup")
    
    if "curl" not in content:
        issues.append("Missing curl for health checks")
    
    if "new_bot.py" not in content:
        issues.append("Missing new_bot.py in CMD")
    
    if issues:
        for issue in issues:
            print_status(f"[WARNING] Dockerfile issue: {issue}", "WARNING")
        return False
    else:
        print_status("[OK] Dockerfile is properly configured for Render", "SUCCESS")
        return True

def validate_requirements():
    """Validate requirements.txt"""
    if not os.path.exists("requirements.txt"):
        print_status("[MISSING] requirements.txt not found", "ERROR")
        return False
    
    with open("requirements.txt", 'r') as f:
        content = f.read()
    
    required_packages = [
        "python-telegram-bot",
        "aiohttp",
        "web3",
        "firebase-admin",
        "python-dotenv"
    ]
    
    missing_packages = []
    for package in required_packages:
        if package not in content:
            missing_packages.append(package)
    
    if missing_packages:
        print_status(f"[ERROR] Missing required packages: {', '.join(missing_packages)}", "ERROR")
        return False
    else:
        print_status("[OK] All required packages found in requirements.txt", "SUCCESS")
        return True

def validate_health_endpoint():
    """Validate health endpoint implementation"""
    if not os.path.exists("new_bot.py"):
        print_status("[MISSING] Main bot file not found: new_bot.py", "ERROR")
        return False
    
    with open("new_bot.py", 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    if "async def health_check" not in content:
        print_status("[ERROR] Health check endpoint not found", "ERROR")
        return False
    
    if "/health" not in content:
        print_status("[ERROR] Health endpoint route not found", "ERROR")
        return False
    
    if "web.json_response" not in content:
        print_status("[WARNING] Health endpoint response not properly implemented", "WARNING")
    
    print_status("[OK] Health endpoint implementation found", "SUCCESS")
    return True

def validate_render_config():
    """Validate Render configuration"""
    if not os.path.exists("render.yaml"):
        print_status("[MISSING] render.yaml not found", "ERROR")
        return False
    
    # Try to validate as YAML
    if not validate_yaml("render.yaml", "Render configuration"):
        return False
    
    with open("render.yaml", 'r') as f:
        content = f.read()
    
    # Check for required elements
    if "type: web" not in content:
        print_status("[WARNING] render.yaml should specify 'type: web'", "WARNING")
    
    if "env: docker" not in content:
        print_status("[WARNING] render.yaml should specify 'env: docker'", "WARNING")
    
    if "dockerfilePath: ./Dockerfile.render" not in content:
        print_status("[WARNING] render.yaml should specify correct dockerfile path", "WARNING")
    
    if "healthCheckPath: /health" not in content:
        print_status("[WARNING] render.yaml should specify health check path", "WARNING")
    
    print_status("[OK] render.yaml configuration is valid", "SUCCESS")
    return True

def check_python_syntax():
    """Check Python syntax in main files"""
    python_files = ["new_bot.py", "config.py", "bot_handlers.py"]
    
    for file in python_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    compile(f.read(), file, 'exec')
                print_status(f"[OK] {file} has valid Python syntax", "SUCCESS")
            except SyntaxError as e:
                print_status(f"[ERROR] {file} has syntax error: {e}", "ERROR")
                return False
            except UnicodeDecodeError:
                print_status(f"[WARNING] {file} has encoding issues, skipping syntax check", "WARNING")
        else:
            print_status(f"[MISSING] {file} not found", "WARNING")
    
    return True

def main():
    """Main validation function"""
    print_status("Validating Render Configuration for TG-Fets Trading Bot")
    print_status("=" * 60)
    
    all_valid = True
    
    # Check required files
    print_status("\nChecking required files...")
    required_files = [
        ("new_bot.py", "Main bot file"),
        ("config.py", "Configuration file"),
        ("requirements.txt", "Python dependencies"),
        ("Dockerfile.render", "Render Dockerfile"),
        ("render.yaml", "Render configuration"),
        ("deploy_render_quick.sh", "Deployment script")
    ]
    
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_valid = False
    
    # Validate configurations
    print_status("\nValidating configurations...")
    
    if not validate_render_config():
        all_valid = False
    
    if not validate_dockerfile("Dockerfile.render"):
        all_valid = False
    
    if not validate_requirements():
        all_valid = False
    
    if not validate_health_endpoint():
        all_valid = False
    
    # Check Python syntax
    print_status("\nChecking Python syntax...")
    if not check_python_syntax():
        all_valid = False
    
    # Summary
    print_status("\n" + "=" * 60)
    if all_valid:
        print_status("All validations passed! Your project is ready for Render deployment.", "SUCCESS")
        print_status("\nNext steps:")
        print_status("1. Run: ./deploy_render_quick.sh")
        print_status("2. Go to https://render.com")
        print_status("3. Connect your GitHub repository")
        print_status("4. Deploy your bot!")
    else:
        print_status("Some validations failed. Please fix the issues above before deploying.", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
