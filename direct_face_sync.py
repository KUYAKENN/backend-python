import requests
import time

print("🔥 DIRECT API SYNC - BYPASSING ALL CHECKS")
print("=" * 60)

try:
    # Direct sync call
    print("🚀 Calling sync-faces-from-db directly...")
    response = requests.post(
        "http://localhost:5000/sync-faces-from-db", 
        timeout=600  # 10 minute timeout
    )
    
    print(f"📡 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SYNC SUCCESSFUL!")
        
        print(f"📊 Message: {result.get('message', 'No message')}")
        
        if 'results' in result and result['results']:
            successful = [r for r in result['results'] if r.get('status') == 'success']
            failed = [r for r in result['results'] if r.get('status') == 'failed']
            
            print(f"\n✅ Successfully processed: {len(successful)} faces")
            print(f"❌ Failed to process: {len(failed)} faces")
            
            # Show successful enrollments
            if successful:
                print("\n🎉 SUCCESSFUL ENROLLMENTS:")
                for success in successful[:10]:  # Show first 10
                    user_name = success.get('user_name', 'Unknown')
                    confidence = success.get('confidence', 0)
                    print(f"   ✅ {user_name} - Confidence: {confidence:.3f}")
                
                if len(successful) > 10:
                    print(f"   ... and {len(successful) - 10} more!")
            
            # Show failures
            if failed:
                print("\n❌ FAILED ENROLLMENTS:")
                for fail in failed[:5]:  # Show first 5
                    user_name = fail.get('user_name', 'Unknown')
                    error = fail.get('message', 'Unknown error')
                    print(f"   ❌ {user_name}: {error}")
                
                if len(failed) > 5:
                    print(f"   ... and {len(failed) - 5} more failed")
        
        else:
            print("ℹ️  No results data in response")
            print(f"Raw response: {result}")
    
    else:
        print(f"❌ SYNC FAILED - Status: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Raw error: {response.text}")

except requests.ConnectionError:
    print("❌ Cannot connect to server!")
    print("Make sure Flask server is running: python main.py")
except requests.Timeout:
    print("⏰ Request timed out - sync may still be running")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "=" * 60)
input("Press Enter to exit...")
