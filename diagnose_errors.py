import requests
import json

print("🔍 DETAILED ERROR DIAGNOSIS")
print("=" * 60)

try:
    # 1. Check server logs by making requests and seeing responses
    print("1. 🏥 Testing all endpoints...")
    
    endpoints = [
        "/health",
        "/faces", 
        "/face-status",
        "/sync-faces-from-db"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing {endpoint}:")
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if endpoint == "/faces":
                        total = data.get('total_count', 0)
                        print(f"   ✅ Found {total} faces")
                        # Check if faces have proper data
                        faces = data.get('faces', [])
                        if faces:
                            sample = faces[0]
                            print(f"   📋 Sample face keys: {list(sample.keys())}")
                            print(f"   📋 Sample user_name: '{sample.get('user_name', 'MISSING')}'")
                            print(f"   📋 Sample confidence: {sample.get('confidence', 'MISSING')}")
                    
                    elif endpoint == "/face-status":
                        users = data.get('data', [])
                        print(f"   📊 Found {len(users)} users")
                        if users:
                            sample = users[0]
                            print(f"   📋 Sample user keys: {list(sample.keys())}")
                        else:
                            print("   ⚠️  No user data returned!")
                    
                    elif endpoint == "/health":
                        print(f"   ✅ Server healthy")
                        
                except ValueError:
                    print(f"   ⚠️  Non-JSON response: {response.text[:200]}")
            else:
                print(f"   ❌ Error: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout on {endpoint}")
        except Exception as e:
            print(f"   ❌ Error on {endpoint}: {str(e)[:100]}")

    # 2. Try to get raw database data
    print(f"\n2. 🗄️  Testing database queries...")
    
    # Check if we can make a sync call to see what happens
    print(f"\n📡 Testing sync endpoint:")
    try:
        sync_response = requests.post("http://localhost:5000/sync-faces-from-db", timeout=30)
        print(f"   Status: {sync_response.status_code}")
        
        if sync_response.status_code == 200:
            sync_data = sync_response.json()
            print(f"   📊 Sync message: {sync_data.get('message', 'No message')}")
            print(f"   📊 Enrolled: {sync_data.get('enrolled_count', 0)}")
            print(f"   📊 Failed: {sync_data.get('failed_count', 0)}")
            
            if 'results' in sync_data:
                print(f"   📊 Results count: {len(sync_data['results'])}")
        else:
            print(f"   ❌ Sync failed: {sync_response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Sync error: {str(e)[:100]}")

    # 3. Check welcome page to see system status
    print(f"\n3. 🏠 Checking welcome page...")
    try:
        welcome_response = requests.get("http://localhost:5000/welcome", timeout=5)
        print(f"   Status: {welcome_response.status_code}")
        if welcome_response.status_code == 200:
            print("   ✅ Welcome page accessible")
    except Exception as e:
        print(f"   ❌ Welcome error: {e}")

except Exception as e:
    print(f"❌ Overall error: {e}")

print("\n" + "=" * 60)
print("🔧 DIAGNOSIS COMPLETE")
print("This will help identify what needs to be fixed!")
input("Press Enter to continue...")
