#!/usr/bin/env python3
"""
Direct database migration script that connects to an existing PostgreSQL database.
Use this if you have PostgreSQL running locally or want to connect to an external database.
"""

import asyncio
import sys
import os
from sqlalchemy import text
from app.database import engine
from app.models import Base

async def create_schema_direct():
    """Create schema directly using raw SQL"""
    
    print("🗄️  Creating Support System Database Schema")
    print("=" * 50)
    
    # Raw SQL for creating the schema
    schema_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
      user_id        SERIAL PRIMARY KEY,
      username       VARCHAR(50) NOT NULL UNIQUE,
      email          VARCHAR(100) NOT NULL UNIQUE,
      display_name   VARCHAR(100),
      role           VARCHAR(50),
      created_at     TIMESTAMP NOT NULL DEFAULT now()
    );

    -- Ticket Categories
    CREATE TABLE IF NOT EXISTS ticketcategories (
      category_id    SERIAL PRIMARY KEY,
      name           VARCHAR(100) NOT NULL UNIQUE,
      description    TEXT
    );

    -- Knowledge Base Articles
    CREATE TABLE IF NOT EXISTS kbarticles (
      kb_id          SERIAL PRIMARY KEY,
      title          VARCHAR(200) NOT NULL,
      summary        TEXT,
      url            VARCHAR(500),
      created_by     INTEGER NOT NULL REFERENCES users(user_id),
      created_at     TIMESTAMP NOT NULL DEFAULT now(),
      updated_at     TIMESTAMP
    );

    -- Tickets
    CREATE TABLE IF NOT EXISTS tickets (
      ticket_id           SERIAL PRIMARY KEY,
      external_ticket_no  VARCHAR(50) UNIQUE,
      requester_id        INTEGER NOT NULL REFERENCES users(user_id),
      assigned_to_id      INTEGER REFERENCES users(user_id),
      category_id         INTEGER REFERENCES ticketcategories(category_id),
      priority            VARCHAR(20) NOT NULL,
      status              VARCHAR(20) NOT NULL,
      created_at          TIMESTAMP NOT NULL DEFAULT now(),
      closed_at           TIMESTAMP,
      sla_due_at          TIMESTAMP,
      subject             VARCHAR(200),
      description         TEXT
    );

    -- Root Causes
    CREATE TABLE IF NOT EXISTS ticketrootcauses (
      rootcause_id   SERIAL PRIMARY KEY,
      ticket_id      INTEGER NOT NULL REFERENCES tickets(ticket_id),
      cause_code     VARCHAR(50),
      description    TEXT,
      identified_at  TIMESTAMP NOT NULL DEFAULT now()
    );

    -- Resolution Steps
    CREATE TABLE IF NOT EXISTS resolutionsteps (
      step_id        SERIAL PRIMARY KEY,
      ticket_id      INTEGER NOT NULL REFERENCES tickets(ticket_id),
      step_order     SMALLINT NOT NULL,
      instructions   TEXT NOT NULL,
      success_flag   BOOLEAN DEFAULT FALSE,
      performed_by   INTEGER REFERENCES users(user_id),
      performed_at   TIMESTAMP
    );

    -- Ticket-KB Links
    CREATE TABLE IF NOT EXISTS ticketkblinks (
      ticket_id      INTEGER NOT NULL REFERENCES tickets(ticket_id),
      kb_id          INTEGER NOT NULL REFERENCES kbarticles(kb_id),
      PRIMARY KEY (ticket_id, kb_id)
    );

    -- Attachments
    CREATE TABLE IF NOT EXISTS attachments (
      attachment_id  SERIAL PRIMARY KEY,
      ticket_id      INTEGER NOT NULL REFERENCES tickets(ticket_id),
      filename       VARCHAR(200),
      file_url       VARCHAR(500),
      uploaded_by    INTEGER REFERENCES users(user_id),
      uploaded_at    TIMESTAMP NOT NULL DEFAULT now()
    );

    -- Keep the original documents table for RAG
    CREATE TABLE IF NOT EXISTS documents (
      id SERIAL PRIMARY KEY,
      title VARCHAR,
      content TEXT,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS ix_tickets_category_status ON tickets(category_id, status);
    CREATE INDEX IF NOT EXISTS ix_tickets_assigned_to ON tickets(assigned_to_id);
    CREATE INDEX IF NOT EXISTS ix_res_steps_ticket_order ON resolutionsteps(ticket_id, step_order);
    CREATE INDEX IF NOT EXISTS ix_tickets_requester ON tickets(requester_id);
    CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON tickets(created_at);
    CREATE INDEX IF NOT EXISTS ix_kbarticles_created_by ON kbarticles(created_by);

    -- Create views
    CREATE OR REPLACE VIEW vw_sla_compliance AS
    SELECT
      category_id,
      COUNT(*) FILTER (WHERE closed_at <= sla_due_at) AS sla_met,
      COUNT(*) FILTER (WHERE closed_at > sla_due_at)  AS sla_breached,
      COUNT(*) AS total
    FROM tickets
    WHERE status = 'Closed'
    GROUP BY category_id;

    -- Insert sample data
    INSERT INTO ticketcategories (name, description) VALUES
      ('Windows Desktop', 'Windows desktop support issues'),
      ('Printers', 'Printer and printing related issues'),
      ('Network', 'Network connectivity and infrastructure'),
      ('Software', 'Application software issues'),
      ('Hardware', 'Computer hardware problems')
    ON CONFLICT (name) DO NOTHING;

    INSERT INTO users (username, email, display_name, role) VALUES
      ('admin', 'admin@company.com', 'System Administrator', 'manager'),
      ('tech1', 'tech1@company.com', 'John Technician', 'technician'),
      ('user1', 'user1@company.com', 'Jane User', 'end-user')
    ON CONFLICT (username) DO NOTHING;

    INSERT INTO kbarticles (title, summary, url, created_by) VALUES
      ('Password Reset Procedure', 'How to reset user passwords in Active Directory', 'https://kb.company.com/password-reset', 1),
      ('Printer Driver Installation', 'Step-by-step guide for installing printer drivers', 'https://kb.company.com/printer-drivers', 1),
      ('VPN Setup Guide', 'Configuration guide for company VPN access', 'https://kb.company.com/vpn-setup', 1)
    ON CONFLICT DO NOTHING;
    """
    
    try:
        async with engine.begin() as conn:
            print("📋 Executing schema creation...")
            await conn.execute(text(schema_sql))
            await conn.commit()
            
        print("✅ Schema created successfully!")
        
        # Verify the creation
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name NOT LIKE 'pg_%'
                AND table_name NOT LIKE 'sql_%'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"  • {table}")
            
            # Check sample data
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM ticketcategories"))
            category_count = result.scalar()
            
            print(f"\n🌱 Sample data inserted:")
            print(f"  • Users: {user_count}")
            print(f"  • Categories: {category_count}")
            
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Direct Database Schema Creation")
    print("Make sure PostgreSQL is running and accessible!")
    print("Database URL from config:", os.getenv("DATABASE_URL", "Not set"))
    print()
    
    success = asyncio.run(create_schema_direct())
    
    if success:
        print("\n🎉 Database schema created successfully!")
        print("\n📚 Available API endpoints:")
        print("  • GET  /support/users - List users")
        print("  • POST /support/users - Create user")
        print("  • GET  /support/tickets - List tickets")
        print("  • POST /support/tickets - Create ticket")
        print("  • GET  /support/categories - List categories")
        print("  • GET  /support/dashboard/stats - Dashboard stats")
        print("\n🚀 Start the application with: uvicorn main:app --reload")
    else:
        print("\n❌ Schema creation failed!")
        sys.exit(1)
