import requests
import time

print("🔥 SUPABASE STORAGE FACE SYNC TEST")
print("=" * 60)

try:
    # Test the sync with updated storage handling
    print("🚀 Calling sync-faces-from-db with storage support...")
    response = requests.post(
        "http://localhost:5000/sync-faces-from-db", 
        timeout=600  # 10 minute timeout
    )
    
    print(f"📡 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SYNC SUCCESSFUL!")
        
        print(f"📊 Message: {result.get('message', 'No message')}")
        print(f"✅ Enrolled: {result.get('enrolled_count', 0)}")
        print(f"❌ Failed: {result.get('failed_count', 0)}")
        
        if 'results' in result and result['results']:
            successful = [r for r in result['results'] if r.get('status') == 'success']
            failed = [r for r in result['results'] if r.get('status') == 'failed']
            
            # Show successful enrollments
            if successful:
                print(f"\n🎉 SUCCESSFUL ENROLLMENTS ({len(successful)}):")
                for success in successful[:10]:  # Show first 10
                    user_name = success.get('message', 'Unknown')
                    confidence = success.get('confidence', 0)
                    print(f"   ✅ {user_name} - Confidence: {confidence:.3f}")
                
                if len(successful) > 10:
                    print(f"   ... and {len(successful) - 10} more!")
            
            # Show failures
            if failed:
                print(f"\n❌ FAILED ENROLLMENTS ({len(failed)}):")
                for fail in failed[:5]:  # Show first 5
                    user_id = fail.get('user_detail_id', 'Unknown')
                    error = fail.get('message', 'Unknown error')
                    print(f"   ❌ {user_id}: {error}")
                
                if len(failed) > 5:
                    print(f"   ... and {len(failed) - 5} more failed")
    
    else:
        print(f"❌ SYNC FAILED - Status: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Raw error: {response.text}")

    # Now check how many faces are enrolled
    print("\n" + "=" * 60)
    print("📊 CHECKING FINAL STATUS...")
    
    faces_response = requests.get("http://localhost:5000/faces", timeout=10)
    if faces_response.status_code == 200:
        faces_data = faces_response.json()
        total_faces = faces_data.get('total_count', 0)
        print(f"✅ Total enrolled faces: {total_faces}")
        
        if total_faces > 0:
            print("🎉 SUCCESS! Faces are now enrolled!")
            print("\n📋 Sample enrolled users:")
            for face in faces_data.get('faces', [])[:5]:
                user_name = face.get('user_name', 'Unknown')
                confidence = face.get('confidence', 0)
                print(f"   - {user_name} (confidence: {confidence:.3f})")
        else:
            print("⚠️  No faces enrolled yet")
    else:
        print(f"❌ Could not check face count: {faces_response.status_code}")

except requests.ConnectionError:
    print("❌ Cannot connect to server!")
    print("Make sure Flask server is running: python main.py")
except requests.Timeout:
    print("⏰ Request timed out - sync may still be running")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "=" * 60)
input("Press Enter to exit...")
