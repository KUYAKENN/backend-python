#!/usr/bin/env python3
"""
Find User Data Tables
This script looks for tables that might contain user profile data
"""

import os
from dotenv import load_dotenv
from src.supabase_service import SupabaseService

# Load environment variables
load_dotenv()

def find_user_tables():
    """Find tables that might contain user data"""
    
    print("🔍 Looking for User Data Tables")
    print("=" * 50)
    
    try:
        supabase_service = SupabaseService()
        
        # More comprehensive list of possible table names
        possible_tables = [
            'users', 'user', 'profiles', 'profile', 'user_profiles', 'user_profile',
            'participants', 'participant', 'members', 'member', 'people', 'person',
            'accounts', 'account', 'visitors', 'visitor', 'registrations', 'registration',
            'attendees', 'attendee', 'contacts', 'contact', 'employees', 'employee',
            'auth_users', 'auth', 'beacon_users', 'beacon_participants', 'conference_participants'
        ]
        
        existing_tables = []
        
        for table_name in possible_tables:
            try:
                response = supabase_service.supabase.table(table_name).select('*').limit(1).execute()
                
                if response.data:
                    print(f"✅ Found table: {table_name}")
                    sample = response.data[0]
                    columns = list(sample.keys())
                    
                    # Look for user-related fields
                    user_fields = []
                    for col in columns:
                        if any(keyword in col.lower() for keyword in ['name', 'email', 'face', 'photo', 'image', 'type', 'company', 'job']):
                            user_fields.append(col)
                    
                    print(f"   📊 Total columns: {len(columns)}")
                    if user_fields:
                        print(f"   🧑 User-related fields: {', '.join(user_fields)}")
                    print(f"   📝 All columns: {', '.join(columns)}")
                    
                    existing_tables.append({
                        'name': table_name,
                        'columns': columns,
                        'user_fields': user_fields,
                        'sample': sample
                    })
                    print()
                    
            except Exception as e:
                if 'does not exist' not in str(e).lower() and 'relation' not in str(e).lower():
                    print(f"⚠️  Error checking table {table_name}: {str(e)[:100]}...")
        
        print(f"📊 Summary: Found {len(existing_tables)} tables with data")
        
        # Analyze which table might be the main user table
        print("\n🎯 Analysis for User Data:")
        for table_info in existing_tables:
            score = 0
            reasons = []
            
            # Score based on user-related fields
            if any('name' in field.lower() for field in table_info['user_fields']):
                score += 3
                reasons.append("has name fields")
            
            if any('email' in field.lower() for field in table_info['user_fields']):
                score += 3
                reasons.append("has email field")
                
            if any('face' in field.lower() or 'photo' in field.lower() or 'image' in field.lower() for field in table_info['user_fields']):
                score += 5
                reasons.append("has face/photo field")
            
            if 'user' in table_info['name'].lower():
                score += 2
                reasons.append("table name contains 'user'")
                
            print(f"   {table_info['name']}: Score {score} - {', '.join(reasons) if reasons else 'no user indicators'}")
        
        return existing_tables
        
    except Exception as e:
        print(f"❌ Error finding user tables: {e}")
        return []

def main():
    """Main function"""
    tables = find_user_tables()
    
    if tables:
        print(f"\n🏁 Found {len(tables)} potential user data tables!")
        print("💡 The Face Recognition app will be updated to use the most suitable table.")
    else:
        print("\n❌ No user data tables found. Please check your database structure.")

if __name__ == "__main__":
    main()
