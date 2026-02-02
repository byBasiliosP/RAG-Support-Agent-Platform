#!/usr/bin/env python3
"""
Seed script to populate the support database with sample data
This script will create users, categories, tickets, and KB articles for testing
"""

import asyncio
import asyncpg
import bcrypt
from datetime import datetime, timedelta
import json

# Database connection
DATABASE_URL = "postgresql://support_user:support_pass_2024@localhost:5433/support_tickets_db"

async def create_sample_data():
    """Create sample data for the support system"""
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("🗑️  Cleaning existing data...")
        # Clear existing data (in proper order due to foreign keys)
        await conn.execute("DELETE FROM ticketkblinks")
        await conn.execute("DELETE FROM attachments")
        await conn.execute("DELETE FROM resolutionsteps")
        await conn.execute("DELETE FROM ticketrootcauses")
        await conn.execute("DELETE FROM tickets")
        await conn.execute("DELETE FROM kbarticles")
        await conn.execute("DELETE FROM ticketcategories")
        await conn.execute("DELETE FROM users")
        
        print("👥 Creating users...")
        # Insert users
        users = [
            (1, 'admin', 'admin@company.com', 'System Administrator', 'admin'),
            (2, 'jsmith', 'john.smith@company.com', 'John Smith', 'technician'),
            (3, 'mjohnson', 'mary.johnson@company.com', 'Mary Johnson', 'technician'),
            (4, 'bwilson', 'bob.wilson@company.com', 'Bob Wilson', 'end-user'),
            (5, 'alee', 'alice.lee@company.com', 'Alice Lee', 'end-user'),
            (6, 'dchen', 'david.chen@company.com', 'David Chen', 'manager'),
        ]
        
        for user in users:
            await conn.execute("""
                INSERT INTO users (user_id, username, email, display_name, role, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
            """, *user)
        
        print("📂 Creating categories...")
        # Insert categories
        categories = [
            (1, 'Windows Desktop', 'Windows desktop and laptop issues'),
            (2, 'Printers', 'Printer setup, drivers, and troubleshooting'),
            (3, 'iPhone', 'iPhone and iOS related issues'),
            (4, 'Android', 'Android device support'),
            (5, 'OneDrive', 'OneDrive sync and storage issues'),
            (6, 'Email', 'Email setup and troubleshooting'),
            (7, 'Network', 'Network connectivity and VPN issues'),
            (8, 'Software', 'Software installation and licensing'),
        ]
        
        for category in categories:
            await conn.execute("""
                INSERT INTO ticketcategories (category_id, name, description)
                VALUES ($1, $2, $3)
            """, *category)
        
        print("📝 Creating KB articles...")
        # Insert KB articles
        kb_articles = [
            (1, 'How to Reset Windows Password', 'Step-by-step guide for password reset', 
             'https://internal-kb.company.com/password-reset', 1),
            (2, 'Printer Driver Installation Guide', 'Installing printer drivers on Windows 10/11',
             'https://internal-kb.company.com/printer-drivers', 2),
            (3, 'iPhone Email Setup', 'Setting up corporate email on iPhone',
             'https://internal-kb.company.com/iphone-email', 3),
            (4, 'OneDrive Sync Issues', 'Troubleshooting OneDrive sync problems',
             'https://internal-kb.company.com/onedrive-sync', 2),
            (5, 'VPN Connection Setup', 'How to connect to corporate VPN',
             'https://internal-kb.company.com/vpn-setup', 1),
        ]
        
        for article in kb_articles:
            await conn.execute("""
                INSERT INTO kbarticles (kb_id, title, summary, url, created_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, *article)
        
        print("🎫 Creating sample tickets...")
        # Insert tickets
        base_date = datetime.now() - timedelta(days=30)
        
        tickets_data = [
            # Open tickets
            (1, 'INC001001', 4, 2, 1, 'Medium', 'Open', base_date + timedelta(days=1),
             None, base_date + timedelta(days=3), 'Cannot log into Windows laptop', 
             'I forgot my password and cannot access my laptop. Tried multiple passwords.'),
            
            (2, 'INC001002', 5, 3, 2, 'High', 'In Progress', base_date + timedelta(days=2),
             None, base_date + timedelta(days=2, hours=4), 'Printer not working', 
             'Office printer stopped working. No one can print documents.'),
            
            (3, 'INC001003', 4, None, 3, 'Low', 'Open', base_date + timedelta(days=5),
             None, base_date + timedelta(days=7), 'iPhone not receiving emails',
             'My iPhone stopped getting work emails since yesterday morning.'),
            
            # Closed tickets (for KB generation testing)
            (4, 'INC001004', 5, 2, 5, 'Medium', 'Closed', base_date + timedelta(days=10),
             base_date + timedelta(days=12), base_date + timedelta(days=12), 'OneDrive not syncing',
             'OneDrive folder showing sync error and files are not updating.'),
            
            (5, 'INC001005', 4, 3, 1, 'High', 'Closed', base_date + timedelta(days=15),
             base_date + timedelta(days=15, hours=2), base_date + timedelta(days=15, hours=4), 'Forgot Windows password',
             'Locked out of Windows computer after vacation. Need password reset.'),
            
            (6, 'INC001006', 5, 2, 7, 'Medium', 'Closed', base_date + timedelta(days=20),
             base_date + timedelta(days=21), base_date + timedelta(days=22), 'Cannot connect to VPN',
             'Working from home but cannot connect to company VPN to access files.'),
        ]
        
        for ticket in tickets_data:
            await conn.execute("""
                INSERT INTO tickets (ticket_id, external_ticket_no, requester_id, assigned_to_id, 
                                   category_id, priority, status, created_at, closed_at, sla_due_at, 
                                   subject, description)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, *ticket)
        
        print("🔍 Creating root causes...")
        # Insert root causes for closed tickets
        root_causes = [
            (1, 4, 'SYNC-001', 'OneDrive cache corruption', base_date + timedelta(days=11)),
            (2, 5, 'AUTH-001', 'Account lockout due to failed attempts', base_date + timedelta(days=15, hours=1)),
            (3, 6, 'NET-001', 'VPN client configuration error', base_date + timedelta(days=20, hours=2)),
        ]
        
        for cause in root_causes:
            await conn.execute("""
                INSERT INTO ticketrootcauses (rootcause_id, ticket_id, cause_code, description, identified_at)
                VALUES ($1, $2, $3, $4, $5)
            """, *cause)
        
        print("📋 Creating resolution steps...")
        # Insert resolution steps for closed tickets
        resolution_steps = [
            # Ticket 4 - OneDrive sync issue
            (1, 4, 1, 'Checked OneDrive sync status in system tray', True, 2, base_date + timedelta(days=11, hours=1)),
            (2, 4, 2, 'Reset OneDrive client cache by running reset command', True, 2, base_date + timedelta(days=11, hours=2)),
            (3, 4, 3, 'Restarted OneDrive service and verified sync resumed', True, 2, base_date + timedelta(days=11, hours=3)),
            
            # Ticket 5 - Password reset
            (4, 5, 1, 'Verified user identity using security questions', True, 3, base_date + timedelta(days=15, hours=1)),
            (5, 5, 2, 'Reset password in Active Directory', True, 3, base_date + timedelta(days=15, hours=1, minutes=30)),
            (6, 5, 3, 'Tested login with new password successfully', True, 3, base_date + timedelta(days=15, hours=2)),
            
            # Ticket 6 - VPN issue
            (7, 6, 1, 'Downloaded latest VPN client configuration file', True, 2, base_date + timedelta(days=20, hours=3)),
            (8, 6, 2, 'Imported new configuration into VPN client', True, 2, base_date + timedelta(days=20, hours=4)),
            (9, 6, 3, 'Successfully connected to VPN and tested file access', True, 2, base_date + timedelta(days=20, hours=5)),
        ]
        
        for step in resolution_steps:
            await conn.execute("""
                INSERT INTO resolutionsteps (step_id, ticket_id, step_order, instructions, 
                                           success_flag, performed_by, performed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, *step)
        
        print("🔗 Creating KB-ticket links...")
        # Link some tickets to KB articles
        kb_links = [
            (5, 1),  # Password reset ticket linked to password reset KB
            (6, 5),  # VPN ticket linked to VPN setup KB
        ]
        
        for link in kb_links:
            await conn.execute("""
                INSERT INTO ticketkblinks (ticket_id, kb_id)
                VALUES ($1, $2)
            """, *link)
        
        print("✅ Sample data created successfully!")
        print(f"📊 Created:")
        print(f"   - {len(users)} users")
        print(f"   - {len(categories)} categories")
        print(f"   - {len(kb_articles)} KB articles")
        print(f"   - {len(tickets_data)} tickets")
        print(f"   - {len(root_causes)} root causes")
        print(f"   - {len(resolution_steps)} resolution steps")
        print(f"   - {len(kb_links)} KB-ticket links")
        
        # Reset sequence counters
        await conn.execute("SELECT setval('users_user_id_seq', (SELECT MAX(user_id) FROM users))")
        await conn.execute("SELECT setval('ticketcategories_category_id_seq', (SELECT MAX(category_id) FROM ticketcategories))")
        await conn.execute("SELECT setval('kbarticles_kb_id_seq', (SELECT MAX(kb_id) FROM kbarticles))")
        await conn.execute("SELECT setval('tickets_ticket_id_seq', (SELECT MAX(ticket_id) FROM tickets))")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Creating sample support system data...")
    asyncio.run(create_sample_data())
