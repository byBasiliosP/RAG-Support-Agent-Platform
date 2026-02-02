#!/usr/bin/env python3
"""
Database migration script to create the support system schema.
This script creates all tables and indexes as specified in the schema.
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import engine
from app.models import Base

# SQL for creating indexes and views
INDEXES_AND_VIEWS_SQL = """
-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_tickets_category_status ON tickets(category_id, status);
CREATE INDEX IF NOT EXISTS ix_tickets_assigned_to ON tickets(assigned_to_id);
CREATE INDEX IF NOT EXISTS ix_res_steps_ticket_order ON resolutionsteps(ticket_id, step_order);
CREATE INDEX IF NOT EXISTS ix_tickets_requester ON tickets(requester_id);
CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS ix_kbarticles_created_by ON kbarticles(created_by);

-- Create SLA compliance view
CREATE OR REPLACE VIEW vw_sla_compliance AS
SELECT
  category_id,
  COUNT(*) FILTER (WHERE closed_at <= sla_due_at) AS sla_met,
  COUNT(*) FILTER (WHERE closed_at > sla_due_at)  AS sla_breached,
  COUNT(*) AS total
FROM tickets
WHERE status = 'Closed'
GROUP BY category_id;

-- Create ticket statistics view
CREATE OR REPLACE VIEW vw_ticket_stats AS
SELECT
  t.category_id,
  c.name as category_name,
  t.status,
  t.priority,
  COUNT(*) as ticket_count,
  AVG(EXTRACT(EPOCH FROM (COALESCE(t.closed_at, NOW()) - t.created_at))/3600) as avg_hours_to_resolve
FROM tickets t
LEFT JOIN ticketcategories c ON t.category_id = c.category_id
GROUP BY t.category_id, c.name, t.status, t.priority;
"""

# Sample data for initial setup
SAMPLE_DATA_SQL = """
-- Insert sample ticket categories
INSERT INTO ticketcategories (name, description) VALUES
  ('Windows Desktop', 'Windows desktop support issues'),
  ('Printers', 'Printer and printing related issues'),
  ('Network', 'Network connectivity and infrastructure'),
  ('Software', 'Application software issues'),
  ('Hardware', 'Computer hardware problems')
ON CONFLICT (name) DO NOTHING;

-- Insert sample users
INSERT INTO users (username, email, display_name, role) VALUES
  ('admin', 'admin@company.com', 'System Administrator', 'manager'),
  ('tech1', 'tech1@company.com', 'John Technician', 'technician'),
  ('user1', 'user1@company.com', 'Jane User', 'end-user')
ON CONFLICT (username) DO NOTHING;

-- Insert sample KB articles
INSERT INTO kbarticles (title, summary, url, created_by) VALUES
  ('Password Reset Procedure', 'How to reset user passwords in Active Directory', 'https://kb.company.com/password-reset', 1),
  ('Printer Driver Installation', 'Step-by-step guide for installing printer drivers', 'https://kb.company.com/printer-drivers', 1),
  ('VPN Setup Guide', 'Configuration guide for company VPN access', 'https://kb.company.com/vpn-setup', 1)
ON CONFLICT DO NOTHING;
"""

async def create_database_schema():
    """Create all database tables, indexes, and views"""
    print("🗄️  Creating database schema...")
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            print("📋 Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            print("📊 Creating indexes and views...")
            # Execute each command separately to avoid asyncpg limitations
            individual_commands = [
                "CREATE INDEX IF NOT EXISTS ix_tickets_category_status ON tickets(category_id, status);",
                "CREATE INDEX IF NOT EXISTS ix_tickets_assigned_to ON tickets(assigned_to_id);",
                "CREATE INDEX IF NOT EXISTS ix_res_steps_ticket_order ON resolutionsteps(ticket_id, step_order);",
                "CREATE INDEX IF NOT EXISTS ix_tickets_requester ON tickets(requester_id);",
                "CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON tickets(created_at);",
                "CREATE INDEX IF NOT EXISTS ix_kbarticles_created_by ON kbarticles(created_by);",
                """CREATE OR REPLACE VIEW vw_sla_compliance AS
                   SELECT
                     category_id,
                     COUNT(*) FILTER (WHERE closed_at <= sla_due_at) AS sla_met,
                     COUNT(*) FILTER (WHERE closed_at > sla_due_at)  AS sla_breached,
                     COUNT(*) AS total
                   FROM tickets
                   WHERE status = 'Closed'
                   GROUP BY category_id;""",
                """CREATE OR REPLACE VIEW vw_ticket_stats AS
                   SELECT
                     t.category_id,
                     c.name as category_name,
                     t.status,
                     t.priority,
                     COUNT(*) as ticket_count,
                     AVG(EXTRACT(EPOCH FROM (COALESCE(t.closed_at, NOW()) - t.created_at))/3600) as avg_hours_to_resolve
                   FROM tickets t
                   LEFT JOIN ticketcategories c ON t.category_id = c.category_id
                   GROUP BY t.category_id, c.name, t.status, t.priority;"""
            ]
            
            for command in individual_commands:
                await conn.execute(text(command))
            
            print("🌱 Inserting sample data...")
            # Split sample data into individual commands
            sample_commands = [
                """INSERT INTO ticketcategories (name, description) VALUES
                   ('Windows Desktop', 'Windows desktop support issues'),
                   ('Printers', 'Printer and printing related issues'),
                   ('Network', 'Network connectivity and infrastructure'),
                   ('Software', 'Application software issues'),
                   ('Hardware', 'Computer hardware problems')
                   ON CONFLICT (name) DO NOTHING;""",
                """INSERT INTO users (username, email, display_name, role) VALUES
                   ('admin', 'admin@company.com', 'System Administrator', 'manager'),
                   ('tech1', 'tech1@company.com', 'John Technician', 'technician'),
                   ('user1', 'user1@company.com', 'Jane User', 'end-user')
                   ON CONFLICT (username) DO NOTHING;""",
                """INSERT INTO kbarticles (title, summary, url, created_by) VALUES
                   ('Password Reset Procedure', 'How to reset user passwords in Active Directory', 'https://kb.company.com/password-reset', 1),
                   ('Printer Driver Installation', 'Step-by-step guide for installing printer drivers', 'https://kb.company.com/printer-drivers', 1),
                   ('VPN Setup Guide', 'Configuration guide for company VPN access', 'https://kb.company.com/vpn-setup', 1)
                   ON CONFLICT DO NOTHING;"""
            ]
            
            for command in sample_commands:
                await conn.execute(text(command))
            
            await conn.commit()
            
        print("✅ Database schema created successfully!")
        
        # Verify tables were created
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"  • {table}")
                
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        sys.exit(1)

async def verify_schema():
    """Verify the schema was created correctly"""
    print("\n🔍 Verifying schema...")
    
    try:
        async with engine.begin() as conn:
            # Check sample data
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM ticketcategories"))
            category_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM kbarticles"))
            kb_count = result.scalar()
            
            print(f"✅ Verification complete:")
            print(f"  • Users: {user_count}")
            print(f"  • Categories: {category_count}")
            print(f"  • KB Articles: {kb_count}")
            
    except Exception as e:
        print(f"⚠️  Verification warning: {e}")

if __name__ == "__main__":
    print("🚀 Support System Database Migration")
    print("=" * 40)
    
    asyncio.run(create_database_schema())
    asyncio.run(verify_schema())
    
    print("\n🎉 Migration completed successfully!")
    print("\nNext steps:")
    print("1. Start your FastAPI application")
    print("2. Visit http://localhost:9000/docs for API documentation")
    print("3. Begin creating tickets and managing support requests")
