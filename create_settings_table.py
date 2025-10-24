#!/usr/bin/env python3
"""
Create system_settings table in production database
This script ensures the system_settings table exists for settings functionality
"""

import os
import psycopg2
from psycopg2 import sql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_settings_table():
    """Create the system_settings table if it doesn't exist"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # Create system_settings table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            setting_type VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'number', 'boolean', 'json')),
            category VARCHAR(50) NOT NULL,
            description TEXT,
            is_editable BOOLEAN DEFAULT TRUE,
            is_sensitive BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cur.execute(create_table_sql)
        logger.info("✅ system_settings table created successfully")
        
        # Insert default settings if table is empty
        cur.execute("SELECT COUNT(*) FROM system_settings")
        count = cur.fetchone()[0]
        
        if count == 0:
            logger.info("Inserting default settings...")
            
            default_settings = [
                ('timezone', 'UTC', 'string', 'system', 'Default system timezone'),
                ('language', 'en', 'string', 'system', 'Default system language'),
                ('maintenance_mode', 'false', 'boolean', 'system', 'System maintenance mode'),
                ('email_notifications', 'true', 'boolean', 'notifications', 'Enable email notifications'),
                ('sms_notifications', 'true', 'boolean', 'notifications', 'Enable SMS notifications'),
                ('push_notifications', 'false', 'boolean', 'notifications', 'Enable push notifications'),
                ('delivery_updates', 'true', 'boolean', 'notifications', 'Enable delivery update notifications'),
                ('hub_updates', 'true', 'boolean', 'notifications', 'Enable hub update notifications'),
            ]
            
            insert_sql = """
            INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cur.executemany(insert_sql, default_settings)
            logger.info(f"✅ Inserted {len(default_settings)} default settings")
        
        # Commit changes
        conn.commit()
        logger.info("✅ Database changes committed successfully")
        
        # Verify table exists and has data
        cur.execute("SELECT COUNT(*) FROM system_settings")
        total_settings = cur.fetchone()[0]
        logger.info(f"✅ system_settings table now has {total_settings} settings")
        
        # Close connections
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating system_settings table: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    logger.info("🔧 Creating system_settings table...")
    success = create_settings_table()
    
    if success:
        logger.info("🎉 system_settings table setup completed successfully!")
    else:
        logger.error("❌ Failed to create system_settings table")
        exit(1)