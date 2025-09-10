#!/usr/bin/env python3
"""
Direct Face Sync Script - Calls the sync API directly
"""
import requests
import json
import time

print("🎯 Direct Face Sync Script")
print("=" * 50)

# Wait for server to be ready
print("⏳ Waiting for server to be ready...")
time.sleep(3)

try:
    # Test server health
    print("🔍 Checking server health...")
    health_response = requests.get("http://localhost:5000/health", timeout=10)
    
    if health_response.status_code == 200:
        print("✅ Server is running!")
        
        # Call sync endpoint
        print("🔄 Starting face synchronization...")
        print("⚠️  This may take several minutes...")
        
        sync_response = requests.post(
            "http://localhost:5000/sync-faces-from-db", 
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minute timeout
        )
        
        if sync_response.status_code == 200:
            result = sync_response.json()
            print("✅ Face synchronization completed!")
            print(f"📊 Result: {result}")
            
            if 'results' in result:
                successful = [r for r in result['results'] if r['status'] == 'success']
                failed = [r for r in result['results'] if r['status'] == 'failed']
                
                print(f"✅ Successfully processed: {len(successful)} faces")
                print(f"❌ Failed to process: {len(failed)} faces")
                
                if successful:
                    print("\n✅ Successfully Enrolled (first 10):")
                    for i, success in enumerate(successful[:10]):
                        user_name = success.get('user_name', 'Unknown')
                        confidence = success.get('confidence', 0)
                        print(f"   {i+1}. {user_name} (confidence: {confidence:.3f})")
                
                if failed:
                    print(f"\n❌ Failed Enrollments (first 5):")
                    for i, failure in enumerate(failed[:5]):
                        user_name = failure.get('user_name', 'Unknown')
                        reason = failure.get('message', 'Unknown error')
                        print(f"   {i+1}. {user_name}: {reason}")
                        
        elif sync_response.status_code == 500:
            error_data = sync_response.json()
            print(f"❌ Server error: {error_data.get('error', 'Unknown error')}")
            
            if 'permission denied for table face_embeddings' in str(error_data):
                print("\n🚨 DATABASE SETUP REQUIRED!")
                print("You need to run the SQL setup first:")
                print("1. Open your Supabase dashboard")
                print("2. Go to SQL Editor")
                print("3. Copy/paste contents of QUICK_SETUP.sql")
                print("4. Run the SQL commands")
                print("5. Then run this script again")
                
        else:
            print(f"❌ Sync failed with status code: {sync_response.status_code}")
            print(f"Response: {sync_response.text}")
            
    else:
        print(f"❌ Server health check failed: {health_response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server!")
    print("Make sure Flask server is running: python main.py")
except requests.exceptions.Timeout:
    print("❌ Request timed out!")
    print("Face processing is taking longer than expected.")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🎯 Face sync script completed!")
input("Press Enter to exit...")
