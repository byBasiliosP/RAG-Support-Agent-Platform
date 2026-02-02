#!/bin/bash

# AI-Powered Customer Support Agent - Development Startup Script
# This script starts the complete development environment with frontend, backend, database, and vector store

set -e

echo "🚀 Starting AI-Powered Customer Support Agent Development Environment"
echo "=================================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

echo "🔧 Building and starting all services..."
docker compose -f docker-compose.dev.yml up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Wait for PostgreSQL to be ready
echo "🔍 Checking PostgreSQL connection..."
until docker compose -f docker-compose.dev.yml exec postgres pg_isready -U support_user -d support_tickets_db; do
    echo "⏳ Waiting for PostgreSQL..."
    sleep 2
done

# Wait for backend to be ready
echo "🔍 Checking backend health..."
until curl -f http://localhost:9000/health >/dev/null 2>&1; do
    echo "⏳ Waiting for backend..."
    sleep 2
done

# Check if database has sample data
echo "🔍 Checking for sample data..."
USER_COUNT=$(curl -s http://localhost:9000/support/users | jq '. | length' 2>/dev/null || echo "0")

if [ "$USER_COUNT" -eq "0" ]; then
    echo "📝 Populating database with sample data..."
    python create_sample_data.py
else
    echo "✅ Database already has sample data ($USER_COUNT users found)"
fi

echo ""
echo "🎉 Development environment is ready!"
echo "=================================="
echo "🌐 Frontend (Next.js):     http://localhost:3000"
echo "🔧 Backend API (FastAPI):  http://localhost:9000"
echo "📚 API Documentation:      http://localhost:9000/docs"
echo "🗄️  PostgreSQL:            localhost:5433"
echo "🔍 ChromaDB:               http://localhost:8001"
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.dev.yml ps
echo ""
echo "🛑 To stop all services: docker compose -f docker-compose.dev.yml down"
echo "📋 To view logs: docker compose -f docker-compose.dev.yml logs -f [service_name]"
echo ""
echo "Happy coding! 🚀"
