#!/usr/bin/env python3
"""
Database Permission and Table Check
This script checks database permissions and creates missing tables if needed.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from supabase import create_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_permissions():
    """Check database permissions and table existence"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not found in .env file")
        return False
    
    print(f"🔗 Connecting to: {supabase_url}")
    print(f"🔑 Using key ending in: ...{supabase_key[-10:]}")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Test 1: Check if we can access user_details (should work)
        print("\n1. 📋 Testing user_details table access...")
        response = supabase.table('user_details').select('id').limit(1).execute()
        if response.data:
            print(f"   ✅ user_details: Found {len(response.data)} records")
        else:
            print("   ⚠️  user_details: No data found")
        
        # Test 2: Check if attendance table exists
        print("\n2. 📅 Testing attendance table access...")
        try:
            response = supabase.table('attendance').select('*').limit(1).execute()
            print(f"   ✅ attendance: Table exists with {len(response.data)} records")
        except Exception as e:
            print(f"   ❌ attendance: Error - {e}")
            print("   💡 Attendance table might not exist or have permission issues")
        
        # Test 3: Check face_embeddings table
        print("\n3. 🧠 Testing face_embeddings table access...")
        try:
            response = supabase.table('face_embeddings').select('id').limit(1).execute()
            print(f"   ✅ face_embeddings: Found {len(response.data)} records")
        except Exception as e:
            print(f"   ❌ face_embeddings: Error - {e}")
        
        # Test 4: List all tables
        print("\n4. 📊 Checking available tables...")
        try:
            # This is a PostgreSQL way to list tables
            response = supabase.rpc('get_tables').execute()
            if response.data:
                print("   ✅ Available tables:")
                for table in response.data:
                    print(f"      - {table}")
        except:
            # Alternative method - try common tables
            common_tables = ['user_details', 'user_accounts', 'attendance', 'face_embeddings', 'face_landmarks']
            print("   📋 Testing common tables:")
            for table_name in common_tables:
                try:
                    response = supabase.table(table_name).select('*').limit(1).execute()
                    print(f"      ✅ {table_name}: Accessible")
                except Exception as e:
                    print(f"      ❌ {table_name}: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_attendance_table():
    """Create attendance table if it doesn't exist"""
    print("\n🔧 Creating attendance table...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS attendance (
        id TEXT NOT NULL DEFAULT ('att_' || substr(gen_random_uuid()::text, 1, 12)) PRIMARY KEY,
        "userId" TEXT NOT NULL,
        "scanDate" DATE NOT NULL DEFAULT CURRENT_DATE,
        "scanTime" TIME NOT NULL DEFAULT CURRENT_TIME,
        "timeIn" TIMESTAMP,
        "timeOut" TIMESTAMP,
        status TEXT DEFAULT 'present' CHECK (status IN ('present', 'late', 'absent')),
        method TEXT DEFAULT 'face_recognition',
        confidence REAL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance("userId", "scanDate");
    CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance("scanDate");
    """
    
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        supabase = create_client(supabase_url, supabase_key)
        
        # Execute the SQL
        response = supabase.rpc('sql', {'query': sql}).execute()
        print("   ✅ Attendance table created successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create attendance table: {e}")
        print("   💡 You may need to run this SQL manually in Supabase dashboard:")
        print(sql)
        return False

def main():
    print("🔍 DATABASE PERMISSION & TABLE CHECKER")
    print("=" * 60)
    
    if not check_database_permissions():
        print("\n❌ Database connection failed!")
        return False
    
    print("\n🎯 RECOMMENDATIONS:")
    print("1. If attendance table is missing, create it manually in Supabase SQL Editor")
    print("2. Make sure you're using the service_role key (not anon key)")
    print("3. Check Row Level Security (RLS) policies if tables exist but give permission errors")
    
    return True

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)