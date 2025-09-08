#!/usr/bin/env python3
"""
Database Schema Inspector
This script helps you understand your Supabase database structure
"""

import os
from dotenv import load_dotenv
from src.supabase_service import SupabaseService

# Load environment variables
load_dotenv()

def inspect_database():
    """Inspect the database structure"""
    
    print("🔍 Database Schema Inspector")
    print("=" * 60)
    
    try:
        # Initialize Supabase service
        supabase_service = SupabaseService()
        
        # List of common table names to check
        table_names = ['users', 'profiles', 'attendance', 'user_profiles', 'participants', 'members']
        
        for table_name in table_names:
            try:
                print(f"\n📋 Checking table: {table_name}")
                
                # Try to get a sample record with all columns
                response = supabase_service.supabase.table(table_name).select('*').limit(1).execute()
                
                if response.data:
                    print(f"✅ Table '{table_name}' exists with {len(response.data)} sample record(s)")
                    
                    # Show column names
                    sample_record = response.data[0]
                    columns = list(sample_record.keys())
                    print(f"   📊 Columns ({len(columns)}): {', '.join(columns)}")
                    
                    # Show sample data (hide sensitive info)
                    print("   📝 Sample record:")
                    for key, value in sample_record.items():
                        if isinstance(value, str) and len(value) > 50:
                            display_value = f"{value[:30]}... (truncated)"
                        else:
                            display_value = value
                        print(f"      {key}: {display_value}")
                        
                else:
                    print(f"✅ Table '{table_name}' exists but is empty")
                    
            except Exception as e:
                error_msg = str(e)
                if 'does not exist' in error_msg.lower() or 'relation' in error_msg.lower():
                    print(f"❌ Table '{table_name}' does not exist")
                else:
                    print(f"⚠️  Error accessing table '{table_name}': {error_msg}")
        
        # Try to get table count for each existing table
        print(f"\n📈 Table Record Counts:")
        for table_name in ['users', 'profiles', 'attendance']:
            try:
                response = supabase_service.supabase.table(table_name).select('*', count='exact').limit(0).execute()
                count = response.count or 0
                print(f"   {table_name}: {count} records")
            except Exception:
                print(f"   {table_name}: Unable to get count")
                
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        return False
    
    return True

def test_queries():
    """Test various query approaches"""
    
    print("\n🧪 Testing Query Approaches")
    print("=" * 40)
    
    try:
        supabase_service = SupabaseService()
        
        # Test 1: Direct users query
        print("\n🔍 Test 1: Direct users query")
        try:
            response = supabase_service.supabase.table('users').select('*').limit(3).execute()
            print(f"✅ Direct users query: {len(response.data)} records")
            if response.data:
                print(f"   Sample user fields: {list(response.data[0].keys())}")
        except Exception as e:
            print(f"❌ Direct users query failed: {e}")
        
        # Test 2: Direct profiles query
        print("\n🔍 Test 2: Direct profiles query")
        try:
            response = supabase_service.supabase.table('profiles').select('*').limit(3).execute()
            print(f"✅ Direct profiles query: {len(response.data)} records")
            if response.data:
                print(f"   Sample profile fields: {list(response.data[0].keys())}")
        except Exception as e:
            print(f"❌ Direct profiles query failed: {e}")
        
        # Test 3: Try the updated get_all_users_with_profiles method
        print("\n🔍 Test 3: Updated get_all_users_with_profiles method")
        try:
            users = supabase_service.get_all_users_with_profiles()
            if users:
                print(f"✅ Updated method: {len(users)} users retrieved")
                if users:
                    print(f"   Sample user data: {list(users[0].keys())}")
                    print(f"   First user: {users[0]['firstName']} {users[0]['lastName']} ({users[0]['email']})")
            else:
                print("❌ Updated method returned None or empty list")
        except Exception as e:
            print(f"❌ Updated method failed: {e}")
    
    except Exception as e:
        print(f"❌ Error testing queries: {e}")

def main():
    """Main function"""
    success = inspect_database()
    
    if success:
        test_queries()
    
    print(f"\n{'=' * 60}")
    print("🏁 Database inspection complete!")
    
    if success:
        print("💡 Use the information above to understand your database structure.")
        print("   The Face Recognition app will now try multiple approaches to load your data.")
    else:
        print("🔧 Please check your Supabase configuration and try again.")

if __name__ == "__main__":
    main()
