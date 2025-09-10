from src.supabase_service import SupabaseService
import json

def check_user_details():
    supabase = SupabaseService()
    
    try:
        user_details = supabase.supabase.table('user_details').select('*').limit(10).execute()
        print('USER_DETAILS TABLE DATA:')
        print('='*50)
        
        users_with_faces = []
        
        for user in user_details.data:
            print(f"ID: {user['id']}")
            print(f"Name: {user.get('firstName', '')} {user.get('lastName', '')}")
            face_url = user.get('faceScannedUrl', None)
            print(f"Face URL: {face_url}")
            
            if face_url and face_url.strip():
                users_with_faces.append(user)
            
            print('-' * 30)
        
        print(f'\nSUMMARY:')
        print(f'Total users: {len(user_details.data)}')
        print(f'Users with face URLs: {len(users_with_faces)}')
        
        if users_with_faces:
            print(f'\nUSERS WITH FACE URLS:')
            for user in users_with_faces:
                print(f"- {user.get('firstName', '')} {user.get('lastName', '')}: {user.get('faceScannedUrl', '')}")
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_user_details()
