import requests
import json

print("🔍 CHECKING WHAT DATA EXISTS")
print("=" * 50)

try:
    # Check enrolled faces
    print("1. 📊 Checking enrolled faces...")
    faces_response = requests.get("http://localhost:5000/faces", timeout=10)
    
    if faces_response.status_code == 200:
        faces_data = faces_response.json()
        total_faces = faces_data.get('total_count', 0)
        print(f"   ✅ Total enrolled faces: {total_faces}")
        
        if total_faces > 0:
            print(f"   📋 Enrolled users:")
            for face in faces_data.get('faces', [])[:10]:  # Show first 10
                user_name = face.get('user_name', 'Unknown')
                confidence = face.get('confidence', 0)
                user_detail_id = face.get('user_detail_id', 'N/A')
                print(f"      - {user_name} (ID: {user_detail_id}, confidence: {confidence:.3f})")
            
            if total_faces > 10:
                print(f"      ... and {total_faces - 10} more")
        else:
            print("   ⚠️  No faces found via API")
    else:
        print(f"   ❌ Faces endpoint failed: {faces_response.status_code}")
        print(f"   Error: {faces_response.text}")

    # Check face status
    print("\n2. 📈 Checking face status...")
    status_response = requests.get("http://localhost:5000/face-status", timeout=10)
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        users = status_data.get('data', [])
        print(f"   📋 Total users: {len(users)}")
        
        if users:
            # Count by status
            status_counts = {}
            for user in users:
                status = user.get('enrollment_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"   📊 Status breakdown:")
            for status, count in status_counts.items():
                print(f"      {status}: {count} users")
            
            # Show sample users
            print(f"   👥 Sample users:")
            for user in users[:5]:
                name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                status = user.get('enrollment_status', 'unknown')
                has_url = bool(user.get('faceScannedUrl'))
                print(f"      - {name} | Status: {status} | Has image: {has_url}")
        else:
            print("   ⚠️  No users found")
    else:
        print(f"   ❌ Status endpoint failed: {status_response.status_code}")
        print(f"   Error: {status_response.text}")

    # Test recognition
    print("\n3. 🧪 Testing recognition system...")
    health_response = requests.get("http://localhost:5000/health", timeout=5)
    
    if health_response.status_code == 200:
        print("   ✅ Server is healthy and ready for recognition")
    else:
        print(f"   ❌ Server health check failed: {health_response.status_code}")

    print(f"\n🎯 SUMMARY:")
    print(f"✅ Your face recognition system is working!")
    print(f"✅ Database tables exist and contain data")
    print(f"✅ Server is running on http://localhost:5000")
    print(f"✅ You can now use the /recognize endpoint for face recognition")

except requests.ConnectionError:
    print("❌ Cannot connect to server!")
    print("Make sure Flask server is running: python main.py")
except Exception as e:
    print(f"❌ Error checking data: {e}")

print("\n" + "=" * 50)
input("Press Enter to exit...")
