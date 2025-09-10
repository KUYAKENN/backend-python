import requests
import json

print("🔍 DETAILED SYSTEM STATUS CHECK")
print("=" * 50)

base_url = "http://localhost:5000"

try:
    # 1. Check server health
    print("1. 🏥 Server Health Check...")
    health = requests.get(f"{base_url}/health", timeout=5)
    print(f"   Status: {health.status_code}")
    if health.status_code == 200:
        print("   ✅ Server is healthy")
    
    # 2. Check face status
    print("\n2. 📊 Face Status Check...")
    status = requests.get(f"{base_url}/face-status", timeout=10)
    print(f"   Status: {status.status_code}")
    
    if status.status_code == 200:
        data = status.json()
        users = data.get('data', [])
        print(f"   📋 Total users found: {len(users)}")
        
        if users:
            # Count by enrollment status
            status_counts = {}
            sample_users = []
            
            for user in users:
                enrollment_status = user.get('enrollment_status', 'unknown')
                status_counts[enrollment_status] = status_counts.get(enrollment_status, 0) + 1
                
                # Collect sample users
                if len(sample_users) < 5:
                    name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                    has_image = bool(user.get('faceScannedUrl'))
                    sample_users.append({
                        'name': name,
                        'status': enrollment_status,
                        'has_image': has_image,
                        'image_url': user.get('faceScannedUrl', '')[:50] + '...' if user.get('faceScannedUrl') else 'None'
                    })
            
            print(f"   📈 Status breakdown:")
            for status, count in status_counts.items():
                print(f"      {status}: {count} users")
            
            print(f"   👥 Sample users:")
            for user in sample_users:
                print(f"      - {user['name']} | Status: {user['status']} | Image: {user['has_image']}")
        else:
            print("   ⚠️  No users returned from API")
    else:
        print(f"   ❌ Face status failed: {status.status_code}")
        print(f"   Error: {status.text}")
    
    # 3. Check enrolled faces count
    print("\n3. 🎯 Enrolled Faces Check...")
    faces = requests.get(f"{base_url}/faces", timeout=10)
    print(f"   Status: {faces.status_code}")
    
    if faces.status_code == 200:
        faces_data = faces.json()
        total_faces = faces_data.get('total_count', 0)
        print(f"   📸 Total enrolled faces: {total_faces}")
        
        if 'faces' in faces_data and faces_data['faces']:
            print(f"   👤 Sample enrolled users:")
            for face in faces_data['faces'][:5]:
                user_name = face.get('user_name', 'Unknown')
                confidence = face.get('confidence', 0)
                print(f"      - {user_name} (confidence: {confidence:.3f})")
    else:
        print(f"   ❌ Faces endpoint failed: {faces.status_code}")
    
    # 4. Manual sync attempt
    print("\n4. 🔄 Manual Sync Test...")
    sync_response = requests.post(f"{base_url}/sync-faces-from-db", timeout=30)
    print(f"   Status: {sync_response.status_code}")
    
    if sync_response.status_code == 200:
        sync_data = sync_response.json()
        print(f"   📊 Sync result: {sync_data.get('message', 'No message')}")
        print(f"   ✅ Enrolled: {sync_data.get('enrolled_count', 0)}")
        print(f"   ❌ Failed: {sync_data.get('failed_count', 0)}")
    else:
        print(f"   ❌ Sync failed: {sync_response.status_code}")
        print(f"   Error: {sync_response.text[:200]}")

except requests.ConnectionError:
    print("❌ Cannot connect to server!")
    print("Make sure Flask server is running: python main.py")
except Exception as e:
    print(f"❌ Error during check: {e}")

print("\n" + "=" * 50)
input("Press Enter to exit...")
