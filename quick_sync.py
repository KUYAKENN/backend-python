#!/usr/bin/env python3
"""
Quick Face Sync - Direct API call to sync faces
Run this AFTER you've executed QUICK_SETUP.sql in Supabase
"""

import requests
import time
import json

def sync_faces():
    print("🔄 Syncing faces from database...")
    print("⏳ This may take several minutes...")
    
    try:
        response = requests.post(
            "http://localhost:5000/sync-faces-from-db",
            timeout=600  # 10 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Face sync completed!")
            print(f"📊 Result: {result.get('message', 'Success')}")
            
            if 'results' in result:
                successful = len([r for r in result['results'] if r['status'] == 'success'])
                failed = len([r for r in result['results'] if r['status'] == 'failed'])
                print(f"✅ Successfully enrolled: {successful} faces")
                print(f"❌ Failed to enroll: {failed} faces")
                
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Run: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Quick Face Sync Tool")
    print("=" * 40)
    print("⚠️  Make sure you've run QUICK_SETUP.sql in Supabase first!")
    print("⚠️  Make sure Flask server is running (python main.py)")
    print("")
    
    input("Press Enter when ready...")
    sync_faces()
    input("\nPress Enter to exit...")
