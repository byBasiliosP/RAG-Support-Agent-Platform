#/bin/bash

# Database Setup Script for Support System
echo "🗄️  Setting up Support System Database"
echo "======================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ Please edit .env file with your actual database credentials"
    echo ""
fi

# Start PostgreSQL with Docker Compose
echo "🐳 Starting PostgreSQL database..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 15

# Check if PostgreSQL is accessible
echo "🔍 Checking database connection..."
python3 -c "
import asyncio
from app.database import engine
async def test_connection():
    try:
        async with engine.begin() as conn:
            result = await conn.execute('SELECT 1')
            print('✅ Database connection successful!')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        exit(1)
asyncio.run(test_connection())
"

# Run database migration
echo "📋 Running database migration..."
python3 migrate_db.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Database setup completed successfully!"
    echo ""
    echo "📊 Database Schema Created:"
    echo "  • users - User management"
    echo "  • ticketcategories - Support categories"
    echo "  • tickets - Support tickets"
    echo "  • kbarticles - Knowledge base"
    echo "  • resolutionsteps - Resolution procedures"
    echo "  • ticketrootcauses - Root cause analysis"
    echo "  • attachments - File attachments"
    echo "  • ticketkblinks - KB-ticket relationships"
    echo ""
    echo "🔗 Sample data inserted:"
    echo "  • 3 users (admin, tech1, user1)"
    echo "  • 5 ticket categories"
    echo "  • 3 KB articles"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Start the application: uvicorn main:app --reload"
    echo "2. Visit http://localhost:9000/docs for API documentation"
    echo "3. Test the support system endpoints"
else
    echo "❌ Database setup failed!"
    exit 1
fi
