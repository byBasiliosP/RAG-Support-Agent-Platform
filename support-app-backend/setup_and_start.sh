#!/bin/bash
# Setup and Start Script for Support App Backend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 Support App Backend Setup${NC}"
echo "==============================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}🔧 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}📋 Copying .env.example to .env${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please update .env with your configuration${NC}"
    else
        echo -e "${RED}❌ No .env.example found either${NC}"
        exit 1
    fi
fi

# Run environment setup
echo -e "${BLUE}🔧 Running environment setup...${NC}"
python setup_env.py

# Ask user what to do next
echo ""
echo -e "${BLUE}🎯 What would you like to do?${NC}"
echo "1) Start the backend server"
echo "2) Run database migrations"
echo "3) Test database connection"
echo "4) Exit"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 Starting backend server...${NC}"
        python main.py
        ;;
    2)
        echo -e "${BLUE}🔄 Running database migrations...${NC}"
        python migrate_db.py
        ;;
    3)
        echo -e "${BLUE}🔍 Testing database connection...${NC}"
        python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from app.database import engine
from sqlalchemy.sql import text

async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            await result.fetchone()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

import asyncio
asyncio.run(test_connection())
"
        ;;
    4)
        echo -e "${YELLOW}👋 Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac
