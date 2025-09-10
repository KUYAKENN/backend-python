import requests
import time

print("🚀 Direct Face Sync")
print("=" * 30)

time.sleep(2)

try:
    print("🔄 Syncing faces...")
    response = requests.post("http://localhost:5000/sync-faces-from-db", timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS!")
        print(f"📊 Message: {result.get('message', 'Completed')}")
        
        if 'results' in result:
            successful = len([r for r in result['results'] if r.get('status') == 'success'])
            failed = len([r for r in result['results'] if r.get('status') == 'failed'])
            print(f"✅ Enrolled: {successful} faces")
            print(f"❌ Failed: {failed} faces")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ Server not running!")
except Exception as e:
    print(f"❌ Error: {e}")

input("Press Enter to exit...")
