#!/bin/bash

# AI-Powered Customer Support Agent - Development Stop Script
# This script stops the complete development environment

set -e

echo "🛑 Stopping AI-Powered Customer Support Agent Development Environment"
echo "====================================================================="

echo "🔧 Stopping all services..."
docker compose -f docker-compose.dev.yml down

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "🔄 To restart: ./start-dev.sh"
echo "🗑️  To remove all data: docker compose -f docker-compose.dev.yml down -v"
