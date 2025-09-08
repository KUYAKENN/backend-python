#!/usr/bin/env python3
"""
Supabase Key Checker
This script helps you determine what type of Supabase key you're using
and guides you to get the correct service_role key.
"""

import os
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_supabase_key():
    """Check the current Supabase key and provide guidance"""
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    print("🔍 Supabase Configuration Checker")
    print("=" * 50)
    
    # Check URL
    if not url:
        print("❌ SUPABASE_URL not found in .env file")
        return False
    else:
        print(f"✅ SUPABASE_URL: {url}")
    
    # Check Key
    if not key:
        print("❌ SUPABASE_KEY not found in .env file")
        return False
    
    # Analyze JWT token
    try:
        decoded = jwt.decode(key, options={"verify_signature": False})
        role = decoded.get('role', 'unknown')
        iss = decoded.get('iss', '')
        ref = decoded.get('ref', '')
        
        print(f"✅ SUPABASE_KEY found (first 20 chars): {key[:20]}...")
        print(f"🔑 Key Type (role): {role}")
        print(f"📊 Issuer: {iss}")
        print(f"🏷️  Reference: {ref}")
        
        if role == 'anon':
            print("\n⚠️  WARNING: You're using an ANONYMOUS key!")
            print("   This key has limited permissions and will cause database errors.")
            print("   For backend services, you need the SERVICE_ROLE key.")
            print("\n📋 How to get the SERVICE_ROLE key:")
            print("   1. Go to your Supabase dashboard")
            print("   2. Navigate to Settings > API")
            print("   3. Look for 'service_role' key (not 'anon' key)")
            print("   4. Copy the service_role key")
            print("   5. Replace SUPABASE_KEY in your .env file")
            print("\n🚨 IMPORTANT: Keep the service_role key SECRET!")
            print("   Never commit it to version control or share it publicly.")
            return False
            
        elif role == 'service_role':
            print("\n✅ PERFECT: You're using the SERVICE_ROLE key!")
            print("   This key has full permissions for backend operations.")
            return True
            
        else:
            print(f"\n❓ UNKNOWN KEY TYPE: {role}")
            print("   This might be a custom key. Ensure it has proper permissions.")
            return False
            
    except Exception as e:
        print(f"❌ Could not decode JWT token: {e}")
        print("   The key might be invalid or corrupted.")
        return False

def main():
    """Main function"""
    is_valid = check_supabase_key()
    
    print("\n" + "=" * 50)
    if is_valid:
        print("🎉 Configuration looks good! Your app should work correctly.")
    else:
        print("🔧 Please fix the configuration issues above.")
        print("   The face recognition app may not work properly until fixed.")

if __name__ == "__main__":
    main()
