#!/bin/bash

# RAG Support Agent Backend Startup Script

echo "🚀 Starting RAG Support Agent Backend..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ Please edit .env file with your actual API keys and settings"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Start services with Docker Compose
echo "🐳 Starting PostgreSQL and ChromaDB..."
docker-compose up -d postgres chromadb

# Wait for services to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Start the FastAPI application
echo "🔥 Starting FastAPI application..."
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
