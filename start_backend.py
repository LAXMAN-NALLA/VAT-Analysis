#!/usr/bin/env python3
"""
Startup script for the VAT Analysis Backend API
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['fastapi', 'uvicorn', 'boto3', 'openai', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ Packages installed successfully!")
    else:
        print("✅ All required packages are installed!")

def check_env_file():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("⚠️  .env file not found!")
        print("Please create a .env file with your API keys:")
        print("""
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET_NAME=vat-analysis-new
OPENAI_API_KEY=your_openai_api_key_here
        """)
        return False
    return True

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting VAT Analysis Backend API...")
    print("🔗 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def main():
    """Main function"""
    print("🏢 VAT Analysis System - Backend API")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ app.py not found in current directory")
        print("Please run this script from the project root directory")
        return
    
    # Check requirements
    check_requirements()
    
    # Check environment file
    if not check_env_file():
        return
    
    # Start backend
    start_backend()

if __name__ == "__main__":
    main()
