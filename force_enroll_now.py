import requests
import json
import base64
import time

def force_enroll_everyone():
    print("🔥 FORCING ENROLLMENT OF ALL USERS NOW!")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # Get all users first
        print("📋 Getting users...")
        response = requests.get(f"{base_url}/face-status", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error getting users: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        users = data.get('data', [])
        
        print(f"✅ Found {len(users)} total users")
        
        # Filter users with face images that aren't enrolled
        users_to_enroll = []
        for user in users:
            if user.get('faceScannedUrl') and user.get('enrollment_status') != 'enrolled':
                users_to_enroll.append(user)
        
        print(f"📸 Users needing enrollment: {len(users_to_enroll)}")
        
        if not users_to_enroll:
            print("ℹ️  No users need enrollment - checking if any are already enrolled...")
            enrolled_users = [u for u in users if u.get('enrollment_status') == 'enrolled']
            print(f"✅ Already enrolled: {len(enrolled_users)} users")
            if enrolled_users:
                print("🎉 All users are already enrolled!")
            return
        
        # Show sample of users to enroll
        print("\n📝 Users to enroll:")
        for user in users_to_enroll[:5]:
            name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            status = user.get('enrollment_status', 'unknown')
            print(f"   - {name} (Status: {status})")
        
        if len(users_to_enroll) > 5:
            print(f"   ... and {len(users_to_enroll) - 5} more")
        
        print(f"\n🚀 Starting enrollment of {len(users_to_enroll)} users...")
        
        enrolled = 0
        failed = 0
        
        for i, user in enumerate(users_to_enroll, 1):
            name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            face_url = user.get('faceScannedUrl')
            user_detail_id = user.get('user_detail_id')
            user_id = user.get('user_id')
            
            print(f"\n🔄 [{i}/{len(users_to_enroll)}] Enrolling: {name}")
            
            try:
                # Download image
                print(f"   📥 Downloading image...")
                img_response = requests.get(face_url, timeout=30)
                if img_response.status_code != 200:
                    print(f"   ❌ Image download failed: {img_response.status_code}")
                    failed += 1
                    continue
                
                # Convert to base64
                img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
                # Prepare enrollment data
                enroll_data = {
                    'image': f"data:image/jpeg;base64,{img_base64}",
                    'user_detail_id': user_detail_id,
                    'user_id': user_id,
                    'user_name': name
                }
                
                print(f"   🧠 Processing face...")
                
                # Enroll via API
                enroll_response = requests.post(
                    f"{base_url}/enroll",
                    json=enroll_data,
                    timeout=120  # 2 minute timeout per user
                )
                
                if enroll_response.status_code == 200:
                    result = enroll_response.json()
                    confidence = result.get('confidence', 0)
                    print(f"   ✅ SUCCESS! Confidence: {confidence:.3f}")
                    enrolled += 1
                else:
                    print(f"   ❌ Enrollment failed: {enroll_response.status_code}")
                    try:
                        error_detail = enroll_response.json()
                        print(f"      Error: {error_detail.get('error', 'Unknown error')}")
                    except:
                        print(f"      Raw error: {enroll_response.text[:200]}")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)[:200]}")
                failed += 1
        
        print("\n" + "=" * 60)
        print("🎉 ENROLLMENT COMPLETE!")
        print(f"✅ Successfully enrolled: {enrolled} users")
        print(f"❌ Failed enrollments: {failed} users")
        print(f"📊 Success rate: {(enrolled/(enrolled+failed)*100):.1f}%" if (enrolled+failed) > 0 else "N/A")
        print("=" * 60)
        
    except requests.ConnectionError:
        print("❌ Can't connect to server! Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Quick server check
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running - proceeding with enrollment")
        else:
            print("⚠️  Server responded but may have issues")
    except:
        print("❌ Server not responding! Start with: python main.py")
        exit(1)
    
    force_enroll_everyone()
    print("\n👋 Press Enter to exit...")
    input()
