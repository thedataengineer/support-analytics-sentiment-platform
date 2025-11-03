#!/usr/bin/env python3
"""
Run SQL initialization script for PostgreSQL.
"""
import os
import psycopg2

# Read SQL file
sql_file = os.path.join(os.path.dirname(__file__), 'init_postgres.sql')
with open(sql_file, 'r') as f:
    sql_script = f.read()

# Connect to database
db_url = os.getenv('DATABASE_URL', 'postgresql://sentiment_user:SentimentPass2024!@localhost:5432/sentiment_db')
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

print("🚀 Running SQL initialization script...")

try:
    # Execute the SQL script
    cur.execute(sql_script)
    print("✅ SQL script executed successfully!")

    # Fetch and display the status
    try:
        results = cur.fetchall()
        if results:
            print("\n📊 Database Status:")
            for row in results:
                print(f"  {row}")
    except:
        pass

except Exception as e:
    print(f"❌ Error executing SQL: {e}")
    raise
finally:
    cur.close()
    conn.close()

print("\n🎉 Database initialization complete!")
