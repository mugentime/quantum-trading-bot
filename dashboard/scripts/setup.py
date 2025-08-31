#!/usr/bin/env python3
"""
Dashboard Setup Script
Automated setup for the Quantum Trading Dashboard
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def setup_backend():
    """Setup Python backend dependencies"""
    print("Setting up backend dependencies...")
    
    # Install Python requirements
    run_command("pip install -r requirements.txt")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    print("Backend setup complete!")

def setup_frontend():
    """Setup React frontend"""
    print("Setting up frontend...")
    
    frontend_dir = "dashboard/frontend"
    
    if not os.path.exists(frontend_dir):
        print(f"Frontend directory {frontend_dir} not found")
        return
        
    # Install npm dependencies
    run_command("npm install", cwd=frontend_dir)
    
    print("Frontend setup complete!")

def build_frontend():
    """Build React frontend for production"""
    print("Building frontend for production...")
    
    frontend_dir = "dashboard/frontend"
    
    if not os.path.exists(frontend_dir):
        print(f"Frontend directory {frontend_dir} not found")
        return
        
    # Build frontend
    run_command("npm run build", cwd=frontend_dir)
    
    print("Frontend build complete!")

def setup_environment():
    """Setup environment variables"""
    print("Setting up environment...")
    
    env_example = ".env.example"
    env_file = ".env"
    
    if os.path.exists(env_example) and not os.path.exists(env_file):
        # Copy example environment file
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print(f"Created {env_file} from {env_example}")
        print("Please update the API keys in .env file")
    elif os.path.exists(env_file):
        print(".env file already exists")
    else:
        # Create basic .env file
        env_content = """# Quantum Trading Dashboard Environment Variables

# Trading Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=true

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
TELEGRAM_NOTIFICATIONS=false

# Dashboard Configuration
PORT=5000
DEBUG=false

# Database (Optional)
DATABASE_URL=sqlite:///dashboard.db

# Security
SECRET_KEY=your_secret_key_here

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Created basic {env_file}")
        print("Please update the API keys and configuration")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    # Check Python
    try:
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print("Error: Python 3.8 or higher is required")
            sys.exit(1)
        print(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - OK")
    except Exception as e:
        print(f"Error checking Python version: {e}")
        sys.exit(1)
    
    # Check Node.js
    try:
        result = run_command("node --version", check=False)
        if result.returncode == 0:
            print(f"Node.js {result.stdout.strip()} - OK")
        else:
            print("Warning: Node.js not found. Frontend build will not be available.")
    except Exception as e:
        print(f"Warning: Could not check Node.js version: {e}")
    
    # Check npm
    try:
        result = run_command("npm --version", check=False)
        if result.returncode == 0:
            print(f"npm {result.stdout.strip()} - OK")
        else:
            print("Warning: npm not found. Frontend build will not be available.")
    except Exception as e:
        print(f"Warning: Could not check npm version: {e}")

def create_systemd_service():
    """Create systemd service file for Linux deployment"""
    if sys.platform != "linux":
        print("Systemd service creation is only available on Linux")
        return
        
    current_dir = os.getcwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Quantum Trading Dashboard
After=network.target

[Service]
Type=simple
User=nobody
WorkingDirectory={current_dir}
Environment=PATH={os.environ.get('PATH', '')}
ExecStart={python_path} dashboard/backend/dashboard_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "/etc/systemd/system/quantum-dashboard.service"
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        print(f"Created systemd service file: {service_file}")
        print("To enable and start the service:")
        print("sudo systemctl enable quantum-dashboard")
        print("sudo systemctl start quantum-dashboard")
    except PermissionError:
        print("Error: Permission denied. Run with sudo to create systemd service")
        print(f"Service content would be written to: {service_file}")
        print(service_content)

def setup_docker():
    """Setup Docker configuration"""
    print("Setting up Docker configuration...")
    
    # Create docker-compose.yml if it doesn't exist
    compose_file = "docker-compose.yml"
    if not os.path.exists(compose_file):
        compose_content = """version: '3.8'

services:
  dashboard:
    build:
      context: .
      dockerfile: dashboard/docker/Dockerfile
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
"""
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        print(f"Created {compose_file}")
    
    # Create .dockerignore if it doesn't exist
    dockerignore_file = ".dockerignore"
    if not os.path.exists(dockerignore_file):
        dockerignore_content = """node_modules
npm-debug.log*
.npm
.git
.gitignore
README.md
.env
.nyc_output
coverage
.cache
dist
logs/*
data/*
backups/*
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
.tox
.venv
env/
venv/
"""
        with open(dockerignore_file, 'w') as f:
            f.write(dockerignore_content)
        print(f"Created {dockerignore_file}")

def main():
    parser = argparse.ArgumentParser(description="Setup Quantum Trading Dashboard")
    parser.add_argument("--backend-only", action="store_true", help="Setup backend only")
    parser.add_argument("--frontend-only", action="store_true", help="Setup frontend only")
    parser.add_argument("--build", action="store_true", help="Build frontend after setup")
    parser.add_argument("--docker", action="store_true", help="Setup Docker configuration")
    parser.add_argument("--systemd", action="store_true", help="Create systemd service")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    print("=== Quantum Trading Dashboard Setup ===")
    
    if args.check_deps:
        check_dependencies()
        return
    
    if not any([args.backend_only, args.frontend_only, args.docker, args.systemd]):
        # Full setup
        check_dependencies()
        setup_environment()
        setup_backend()
        setup_frontend()
        
        if args.build:
            build_frontend()
            
        print("\n=== Setup Complete! ===")
        print("Next steps:")
        print("1. Update your API keys in .env file")
        print("2. Run the dashboard: python dashboard/backend/dashboard_server.py")
        print("3. Open http://localhost:5000 in your browser")
        return
    
    if args.backend_only:
        setup_backend()
    
    if args.frontend_only:
        setup_frontend()
        if args.build:
            build_frontend()
    
    if args.docker:
        setup_docker()
    
    if args.systemd:
        create_systemd_service()
    
    print("Setup tasks completed!")

if __name__ == "__main__":
    main()