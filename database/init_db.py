#!/usr/bin/env python
"""
Database initialization script for SmartCare
Run this once to set up the database
"""

import MySQLdb
import sys
import os

# Database connection for initial setup (no db specified)
try:
    conn = MySQLdb.connect(
        host='localhost',
        user='root',
        passwd='',
    )
    cursor = conn.cursor()
    
    # Read and execute the SQL file from this script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, 'smartcare_db.sql')
    with open(sql_path, 'r') as f:
        sql_content = f.read()
    
    # Execute each statement
    for statement in sql_content.split(';'):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print("✅ All tables created: users, diet_data, contact_messages")
    
except MySQLdb.Error as e:
    print(f"❌ Database Error: {e}")
    sys.exit(1)
except FileNotFoundError:
    print("❌ smartcare_db.sql not found in database folder")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
