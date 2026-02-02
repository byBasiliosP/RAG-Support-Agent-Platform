#!/bin/bash
# Simple activation script for the virtual environment

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup_and_start.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    echo "✅ Environment variables will be loaded from .env"
else
    echo "⚠️  No .env file found"
fi

echo "✅ Virtual environment activated!"
echo "💡 You can now run:"
echo "   python main.py              # Start the backend server"
echo "   python setup_env.py         # Validate environment"
echo "   python migrate_db.py        # Run database migrations"
echo ""
echo "📝 To deactivate the virtual environment, run: deactivate"

# Start a new shell with the virtual environment activated
exec "$SHELL"
