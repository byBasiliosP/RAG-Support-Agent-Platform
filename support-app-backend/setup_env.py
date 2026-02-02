#!/usr/bin/env python3
"""
Environment Setup and Validation Script for Support App Backend
This script handles:
1. Virtual environment activation
2. Environment variable loading and validation
3. Database connection testing
4. Dependencies verification
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import importlib.util

def check_virtual_env():
    """Check if we're running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def activate_virtual_env():
    """Activate the virtual environment."""
    venv_path = Path(__file__).parent / "venv"
    
    if not venv_path.exists():
        print("❌ Virtual environment not found. Creating one...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created.")
    
    # Check if we're already in a virtual environment
    if check_virtual_env():
        print("✅ Already running in virtual environment")
        return True
    
    # Get the activation script path
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
    
    if not activate_script.exists():
        print(f"❌ Activation script not found: {activate_script}")
        return False
    
    print(f"🔄 To activate virtual environment manually, run:")
    print(f"   source {activate_script}")
    return True

def install_dependencies():
    """Install required dependencies."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        print("🔄 Installing dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def load_environment_variables():
    """Load and validate environment variables."""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Try to import python-dotenv
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("❌ python-dotenv not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv"], check=True)
        from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv(env_file)
    print("✅ Environment variables loaded from .env")
    
    # Validate critical environment variables
    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def display_environment_info():
    """Display current environment information."""
    print("\n" + "="*50)
    print("🔍 ENVIRONMENT INFORMATION")
    print("="*50)
    
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"🔧 Virtual Environment: {'✅ Active' if check_virtual_env() else '❌ Not Active'}")
    
    # Display key environment variables (without sensitive data)
    env_vars_to_show = {
        "DATABASE_URL": os.getenv("DATABASE_URL", "Not set"),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "Not set"),
        "HOST": os.getenv("HOST", "Not set"),
        "PORT": os.getenv("PORT", "Not set"),
        "DEBUG": os.getenv("DEBUG", "Not set"),
        "CHROMA_HOST": os.getenv("CHROMA_HOST", "Not set"),
        "CHROMA_PORT": os.getenv("CHROMA_PORT", "Not set"),
    }
    
    print("\n🔧 Environment Variables:")
    for key, value in env_vars_to_show.items():
        # Mask sensitive information
        if "PASSWORD" in key or "KEY" in key:
            display_value = "***MASKED***" if value != "Not set" else "Not set"
        else:
            display_value = value
        print(f"   {key}: {display_value}")
    
    # Check if OpenAI API key is set (without revealing it)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"   OPENAI_API_KEY: ***SET*** (length: {len(openai_key)})")
    else:
        print("   OPENAI_API_KEY: ❌ NOT SET")

def test_database_connection():
    """Test database connection."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.sql import text
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
        
        print("🔄 Testing database connection...")
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✅ Database connection successful")
        return True
        
    except ImportError:
        print("⚠️  SQLAlchemy not installed, skipping database test")
        return None
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "python-dotenv",
        "langchain",
        "openai"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def main():
    """Main setup function."""
    print("🚀 Support App Backend Environment Setup")
    print("="*50)
    
    # Step 1: Check/activate virtual environment
    if not activate_virtual_env():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not check_dependencies():
        if not install_dependencies():
            sys.exit(1)
    
    # Step 3: Load environment variables
    if not load_environment_variables():
        sys.exit(1)
    
    # Step 4: Display environment info
    display_environment_info()
    
    # Step 5: Test database connection (optional)
    test_database_connection()
    
    print("\n🎉 Environment setup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. To activate the virtual environment manually:")
    print("      source venv/bin/activate")
    print("   2. To start the backend server:")
    print("      python main.py")
    print("   3. To run with uvicorn directly:")
    print("      uvicorn main:app --host 0.0.0.0 --port 9000 --reload")

if __name__ == "__main__":
    main()
