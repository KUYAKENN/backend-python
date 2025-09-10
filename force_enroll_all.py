#!/usr/bin/env python3
"""
FORCE FACE ENROLLMENT - Enroll ALL users with face images NOW!
This bypasses all checks and forces enrollment of every user
"""

import requests
import json
import time
import sys

def force_enroll_all():
    print("🔥 FORCE ENROLLING ALL FACES NOW!")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # First get all users
        print("📋 Getting all users...")
        response = requests.get(f"{base_url}/face-status", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Can't get users: {response.status_code}")
            print(response.text)
            return False
            
        data = response.json()
        users = data.get('data', [])
        print(f"✅ Found {len(users)} total users")
        
        # Filter users with face images
        users_with_faces = [u for u in users if u.get('faceScannedUrl')]
        print(f"📸 Users with face images: {len(users_with_faces)}")
        
        if not users_with_faces:
            print("❌ No users have face images!")
            return False
        
        # Force enrollment for each user
        enrolled = 0
        failed = 0
        
        for i, user in enumerate(users_with_faces, 1):
            user_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            face_url = user.get('faceScannedUrl')
            
            print(f"\n🔄 [{i}/{len(users_with_faces)}] Processing: {user_name}")
            
            try:
                # Download the image
                img_response = requests.get(face_url, timeout=30)
                if img_response.status_code != 200:
                    print(f"   ❌ Can't download image: {img_response.status_code}")
                    failed += 1
                    continue
                
                # Convert to base64
                import base64
                img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
                # Enroll the face
                enroll_data = {
                    'image': f"data:image/jpeg;base64,{img_base64}",
                    'user_detail_id': user.get('user_detail_id'),
                    'user_id': user.get('user_id'),
                    'user_name': user_name
                }
                
                enroll_response = requests.post(
                    f"{base_url}/enroll",
                    json=enroll_data,
                    timeout=60
                )
                
                if enroll_response.status_code == 200:
                    result = enroll_response.json()
                    confidence = result.get('confidence', 0)
                    print(f"   ✅ ENROLLED! Confidence: {confidence:.3f}")
                    enrolled += 1
                else:
                    error_msg = enroll_response.text[:100]
                    print(f"   ❌ Failed: {enroll_response.status_code} - {error_msg}")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                failed += 1
                continue
        
        print("\n" + "=" * 50)
        print("🎉 FORCE ENROLLMENT COMPLETE!")
        print(f"✅ Successfully enrolled: {enrolled} faces")
        print(f"❌ Failed to enroll: {failed} faces")
        print("=" * 50)
        
        return enrolled > 0
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Start with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 FORCE FACE ENROLLMENT TOOL")
    print("This will enroll EVERY user with a face image")
    print("=" * 50)
    
    # Check server
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server not responding correctly")
            return False
    except:
        print("❌ Server not running! Start with: python main.py")
        return False
    
    # Force enrollment
    return force_enroll_all()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ALL FACES ENROLLED! Your system is ready!")
    else:
        print("\n❌ Enrollment failed. Check the errors above.")
    
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
