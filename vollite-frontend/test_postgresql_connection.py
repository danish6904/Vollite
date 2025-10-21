# test_connection.py
# Test script to verify PostgreSQL connection

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgresql_connection():
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')

        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False

        print(f"🔗 Connecting to: {database_url.replace('g3flazt8j', '***')}")

        # Create engine
        engine = create_engine(database_url)

        # Test connection
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful!")
            print(f"📋 Version: {version}")

            # Test database exists
            result = connection.execute(text("SELECT current_database()"))
            database = result.fetchone()[0]
            print(f"📊 Connected to database: {database}")

            # Test user permissions
            result = connection.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"👤 Connected as user: {user}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    if success:
        print("\n🎉 PostgreSQL is ready for volLite!")
    else:
        print("\n🚨 Please check your PostgreSQL configuration")