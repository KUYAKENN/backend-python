from supabase import create_client, Client
import os
from typing import List, Dict, Optional
import logging
from datetime import date, datetime, timezone, timedelta
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.supabase: Client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Supabase client"""
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            
            # Log key type for debugging (first few characters only)
            key_prefix = key[:20] if key else 'None'
            logger.info(f"Initializing Supabase with URL: {url}")
            logger.info(f"Using key starting with: {key_prefix}...")
            
            # Determine key type based on JWT payload
            try:
                import jwt
                decoded = jwt.decode(key, options={"verify_signature": False})
                role = decoded.get('role', 'unknown')
                logger.info(f"Supabase key role: {role}")
                
                if role == 'anon':
                    logger.warning("⚠️  Using anonymous key - this may have limited permissions")
                    logger.warning("   Consider using service_role key for backend services")
                elif role == 'service_role':
                    logger.info("✅ Using service_role key - full permissions available")
                    
            except Exception as jwt_error:
                logger.warning(f"Could not decode JWT to check role: {jwt_error}")
            
            self.supabase = create_client(url, key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise e
    
    def get_ph_datetime(self):
        """Get current datetime in Philippine timezone (UTC+8)"""
        ph_timezone = timezone(timedelta(hours=8))
        return datetime.now(ph_timezone)
    
    def get_storage_url(self, file_path: str, bucket_name: str = 'user-profile') -> str:
        """Convert storage file path to accessible URL"""
        try:
            # If it's already a full URL, return as is
            if file_path.startswith('http'):
                return file_path
            
            # Remove leading slash if present
            file_path = file_path.lstrip('/')
            
            # Create a signed URL for the file (valid for 1 hour)
            response = self.supabase.storage.from_(bucket_name).create_signed_url(file_path, 3600)
            
            if response:
                base_url = os.getenv('SUPABASE_URL')
                signed_url = f"{base_url}/storage/v1/object/sign/{bucket_name}/{file_path}?token={response['token']}"
                logger.debug(f"Created signed URL for {file_path}")
                return signed_url
            else:
                logger.warning(f"Could not create signed URL for {file_path}")
                # Fallback to public URL
                return f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{bucket_name}/{file_path}"
                
        except Exception as e:
            logger.error(f"Error creating storage URL for {file_path}: {e}")
            # Fallback to direct public URL
            base_url = os.getenv('SUPABASE_URL')
            return f"{base_url}/storage/v1/object/public/{bucket_name}/{file_path.lstrip('/')}"
    
    def download_storage_file(self, file_path: str, bucket_name: str = 'user-profile') -> Optional[bytes]:
        """Download file from Supabase Storage"""
        try:
            # Remove leading slash if present
            file_path = file_path.lstrip('/')
            
            # Download the file
            response = self.supabase.storage.from_(bucket_name).download(file_path)
            
            if response:
                logger.debug(f"Successfully downloaded {file_path} from {bucket_name}")
                return response
            else:
                logger.warning(f"Could not download {file_path} from {bucket_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading {file_path} from {bucket_name}: {e}")
            return None
    
    def get_ph_date(self):
        """Get current date in Philippine timezone (UTC+8)"""
        return self.get_ph_datetime().date()
    
    def convert_utc_to_ph_time(self, utc_time_str: str) -> str:
        """Convert UTC timestamp string to Philippine time for display"""
        try:
            # Parse the UTC timestamp (assuming it's stored as UTC)
            if isinstance(utc_time_str, str):
                # Handle different timestamp formats
                if 'T' in utc_time_str:
                    if '+' in utc_time_str or 'Z' in utc_time_str:
                        # Already has timezone info
                        dt = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
                    else:
                        # Assume UTC if no timezone info
                        dt = datetime.fromisoformat(utc_time_str).replace(tzinfo=timezone.utc)
                else:
                    # Handle format like "2025-08-27 16:00:30.374903"
                    dt = datetime.fromisoformat(utc_time_str).replace(tzinfo=timezone.utc)
                
                # Convert to Philippine timezone
                ph_timezone = timezone(timedelta(hours=8))
                ph_time = dt.astimezone(ph_timezone)
                return ph_time.isoformat()
            return utc_time_str
        except Exception as e:
            logger.error(f"Error converting timestamp: {e}")
            return utc_time_str
    
    def test_database_access(self) -> Dict:
        """Test database connectivity and return detailed information"""
        results = {
            'connection_status': 'Unknown',
            'environment_check': {},
            'table_access': {},
            'error_details': None
        }
        
        try:
            # Check environment variables
            results['environment_check'] = {
                'supabase_url': os.getenv('SUPABASE_URL') is not None,
                'supabase_key': os.getenv('SUPABASE_KEY') is not None,
                'url_format': os.getenv('SUPABASE_URL', '').startswith('https://') if os.getenv('SUPABASE_URL') else False
            }
            
            # Test simple connection
            try:
                # Try to access a system table that should always exist
                response = self.supabase.table('users').select('count', count='exact').limit(0).execute()
                results['connection_status'] = 'SUCCESS'
                results['table_access']['users_accessible'] = True
                results['table_access']['users_count'] = response.count
                
            except Exception as table_error:
                results['connection_status'] = 'FAILED'
                results['table_access']['users_accessible'] = False
                results['error_details'] = str(table_error)
            
            # Test profiles table if users table works
            if results['table_access'].get('users_accessible'):
                try:
                    response = self.supabase.table('profiles').select('count', count='exact').limit(0).execute()
                    results['table_access']['profiles_accessible'] = True
                    results['table_access']['profiles_count'] = response.count
                except Exception as profiles_error:
                    results['table_access']['profiles_accessible'] = False
                    results['table_access']['profiles_error'] = str(profiles_error)
            
            # Test attendance table
            if results['table_access'].get('users_accessible'):
                try:
                    response = self.supabase.table('attendance').select('count', count='exact').limit(0).execute()
                    results['table_access']['attendance_accessible'] = True
                    results['table_access']['attendance_count'] = response.count
                except Exception as attendance_error:
                    results['table_access']['attendance_accessible'] = False
                    results['table_access']['attendance_error'] = str(attendance_error)
        
        except Exception as e:
            results['connection_status'] = 'ERROR'
            results['error_details'] = str(e)
        
        return results
    
    def get_all_users_with_details(self) -> Optional[List[Dict]]:
        """Get all users with their detailed profile information from user_details table"""
        try:
            # Query users with their details
            response = self.supabase.table('user_details').select('*').execute()
            
            if response.data:
                users = []
                for user_detail in response.data:
                    user_data = {
                        'id': user_detail.get('userId', ''),  # Use userId from user_details as main ID
                        'detail_id': user_detail.get('id', ''),
                        'firstName': user_detail.get('firstName', ''),
                        'lastName': user_detail.get('lastName', ''),
                        'middleName': user_detail.get('middleName', ''),
                        'suffix': user_detail.get('suffix', ''),
                        'preferredName': user_detail.get('preferredName', ''),
                        'faceScannedUrl': user_detail.get('faceScannedUrl', ''),
                        'position': user_detail.get('position', ''),
                        'gender': user_detail.get('gender', ''),
                        'ageBracket': user_detail.get('ageBracket', ''),
                        'nationality': user_detail.get('nationality', ''),
                        # Add userType and email for compatibility
                        'userType': 'attendee',  # Default type
                        'email': f"{user_detail.get('firstName', '').lower()}.{user_detail.get('lastName', '').lower()}@event.com"
                    }
                    users.append(user_data)
                
                logger.info(f"Successfully retrieved {len(users)} users with details")
                return users
            else:
                logger.warning("No user details found")
                return []
                
        except Exception as e:
            logger.error(f"Error getting users with details: {e}")
            return None
    
    def save_face_embedding(self, user_detail_id: str, user_id: str, embedding_data: Dict) -> Dict:
        """Save face embedding data to the database"""
        try:
            # Convert numpy array to list for JSON storage
            if hasattr(embedding_data.get('embedding'), 'tolist'):
                embedding_list = embedding_data['embedding'].tolist()
            else:
                embedding_list = embedding_data['embedding']
            
            face_data = {
                'user_detail_id': user_detail_id,
                'user_id': user_id,
                'embedding': embedding_list,
                'embedding_size': len(embedding_list),
                'confidence': float(embedding_data.get('confidence', 0.0)),
                'face_quality_score': float(embedding_data.get('face_quality_score', 0.0)),
                'source_url': embedding_data.get('source_url', ''),
                'enrollment_method': embedding_data.get('enrollment_method', 'api')
            }
            
            # Insert or update face embedding
            response = self.supabase.table('face_embeddings').upsert(
                face_data, 
                on_conflict='user_detail_id'
            ).execute()
            
            if response.data:
                logger.info(f"Successfully saved face embedding for user_detail_id {user_detail_id}")
                return {'success': True, 'data': response.data[0]}
            else:
                logger.error("No data returned when saving face embedding")
                return {'success': False, 'error': 'No data returned'}
                
        except Exception as e:
            logger.error(f"Error saving face embedding: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_face_landmarks(self, user_detail_id: str, user_id: str, landmarks_data: Dict) -> Dict:
        """Save face landmarks data to the database"""
        try:
            landmark_data = {
                'user_detail_id': user_detail_id,
                'user_id': user_id,
                'landmarks': landmarks_data.get('landmarks', []),
                'bbox': landmarks_data.get('bbox', []),
                'face_area': landmarks_data.get('face_area'),
                'face_angle': landmarks_data.get('face_angle'),
                'age': landmarks_data.get('age'),
                'gender': landmarks_data.get('gender'),
                'emotion': landmarks_data.get('emotion', {}),
                'face_attributes': landmarks_data.get('face_attributes', {})
            }
            
            # Insert or update face landmarks
            response = self.supabase.table('face_landmarks').upsert(
                landmark_data, 
                on_conflict='user_detail_id'
            ).execute()
            
            if response.data:
                logger.info(f"Successfully saved face landmarks for user_detail_id {user_detail_id}")
                return {'success': True, 'data': response.data[0]}
            else:
                logger.error("No data returned when saving face landmarks")
                return {'success': False, 'error': 'No data returned'}
                
        except Exception as e:
            logger.error(f"Error saving face landmarks: {e}")
            return {'success': False, 'error': str(e)}
    
    def log_face_enrollment(self, user_detail_id: str, user_id: str, enrollment_data: Dict) -> Dict:
        """Log face enrollment attempt"""
        try:
            log_data = {
                'user_detail_id': user_detail_id,
                'user_id': user_id,
                'enrollment_status': enrollment_data.get('enrollment_status', 'failed'),
                'face_count_detected': enrollment_data.get('face_count_detected', 0),
                'face_quality_score': enrollment_data.get('face_quality_score'),
                'error_message': enrollment_data.get('error_message'),
                'image_source': enrollment_data.get('image_source', 'api'),
                'source_url': enrollment_data.get('source_url'),
                'image_metadata': enrollment_data.get('image_metadata', {}),
                'processing_time_ms': enrollment_data.get('processing_time_ms')
            }
            
            response = self.supabase.table('face_enrollment_log').insert(log_data).execute()
            
            if response.data:
                logger.info(f"Successfully logged face enrollment for user_detail_id {user_detail_id}")
                return {'success': True, 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'No data returned'}
                
        except Exception as e:
            logger.error(f"Error logging face enrollment: {e}")
            return {'success': False, 'error': str(e)}
    
    def log_face_recognition(self, recognition_data: Dict) -> Dict:
        """Log face recognition attempt"""
        try:
            log_data = {
                'session_id': recognition_data.get('session_id'),
                'recognized_user_detail_id': recognition_data.get('recognized_user_detail_id'),
                'recognized_user_id': recognition_data.get('recognized_user_id'),
                'similarity_score': recognition_data.get('similarity_score'),
                'threshold_used': recognition_data.get('threshold_used', 0.5),
                'candidates_count': recognition_data.get('candidates_count', 0),
                'recognition_status': recognition_data.get('recognition_status', 'error'),
                'error_message': recognition_data.get('error_message'),
                'processing_time_ms': recognition_data.get('processing_time_ms'),
                'image_metadata': recognition_data.get('image_metadata', {}),
                'all_similarities': recognition_data.get('all_similarities', {}),
                'attendance_marked': recognition_data.get('attendance_marked', False),
                'attendance_id': recognition_data.get('attendance_id'),
                'ip_address': recognition_data.get('ip_address'),
                'user_agent': recognition_data.get('user_agent')
            }
            
            response = self.supabase.table('face_recognition_log').insert(log_data).execute()
            
            if response.data:
                logger.info(f"Successfully logged face recognition attempt")
                return {'success': True, 'data': response.data[0]}
            else:
                return {'success': False, 'error': 'No data returned'}
                
        except Exception as e:
            logger.error(f"Error logging face recognition: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_users_for_face_enrollment(self) -> List[Dict]:
        """Get users who have face images but are not yet enrolled"""
        try:
            # Query to get users with face images that haven't been enrolled yet
            response = self.supabase.rpc('get_users_ready_for_enrollment').execute()
            
            if not response.data:
                # Fallback to manual query if RPC doesn't exist
                response = self.supabase.table('user_details').select(
                    'id, "userId", "firstName", "lastName", "middleName", "faceScannedUrl"'
                ).neq('faceScannedUrl', '').is_('faceScannedUrl', 'not.null').execute()
                
                if response.data:
                    # Filter out already enrolled users
                    enrolled_response = self.supabase.table('face_embeddings').select('user_detail_id').execute()
                    enrolled_ids = {item['user_detail_id'] for item in enrolled_response.data} if enrolled_response.data else set()
                    
                    users_to_enroll = []
                    for user in response.data:
                        if user['id'] not in enrolled_ids:
                            users_to_enroll.append(user)
                    
                    logger.info(f"Found {len(users_to_enroll)} users ready for face enrollment")
                    return users_to_enroll
            
            return response.data if response.data else []
                
        except Exception as e:
            logger.error(f"Error getting users for face enrollment: {e}")
            return []
    
    def get_face_embeddings(self) -> List[Dict]:
        """Get all face embeddings from database"""
        try:
            response = self.supabase.table('face_embeddings').select(
                'user_detail_id, user_id, embedding, confidence'
            ).execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} face embeddings")
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting face embeddings: {e}")
            return []
    
    def get_user_face_status(self) -> List[Dict]:
        """Get face enrollment status for all users"""
        try:
            # Use the view we created
            response = self.supabase.table('user_face_status').select('*').execute()
            
            if response.data:
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting user face status: {e}")
            return []
            return False
    
    def log_face_recognition(self, user_id: str, recognition_data: Dict) -> bool:
        """Log a face recognition event"""
        try:
            log_data = {
                'user_id': user_id,
                'recognition_confidence': recognition_data.get('confidence', 0.0),
                'recognition_method': recognition_data.get('method', 'camera'),
                'bbox_x1': recognition_data.get('bbox', [None])[0],
                'bbox_y1': recognition_data.get('bbox', [None, None])[1] if len(recognition_data.get('bbox', [])) > 1 else None,
                'bbox_x2': recognition_data.get('bbox', [None, None, None])[2] if len(recognition_data.get('bbox', [])) > 2 else None,
                'bbox_y2': recognition_data.get('bbox', [None, None, None, None])[3] if len(recognition_data.get('bbox', [])) > 3 else None,
                'landmarks': recognition_data.get('landmarks', []),
                'attendance_id': recognition_data.get('attendance_id'),
                'device_info': recognition_data.get('device_info', {}),
                'session_id': recognition_data.get('session_id')
            }
            
            response = self.supabase.table('face_recognition_logs').insert(log_data).execute()
            
            if response.data:
                logger.info(f"Successfully logged face recognition for user {user_id}")
                return True
            else:
                logger.error(f"Failed to log face recognition for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging face recognition: {e}")
            return False
    
    def get_all_users_with_profiles(self) -> Optional[List[Dict]]:
        """Get all users with their profile information - works with user_details and user_accounts tables"""
        try:
            logger.info("Fetching users using actual database schema (user_details + user_accounts)")
            
            # Get user details (names, face images, etc.)
            user_details_response = self.supabase.table('user_details').select('*').execute()
            user_details_by_id = {detail['userId']: detail for detail in user_details_response.data}
            
            # Get user accounts (email, phone, etc.)
            user_accounts_response = self.supabase.table('user_accounts').select('*').execute()
            user_accounts_by_id = {account['userId']: account for account in user_accounts_response.data}
            
            # Also check if we have additional data from visitors table
            visitors_data = {}
            try:
                visitors_response = self.supabase.table('visitors').select('*').execute()
                visitors_data = {visitor['userId']: visitor for visitor in visitors_response.data if visitor.get('userId')}
                logger.info(f"Found {len(visitors_data)} visitor records")
            except Exception as e:
                logger.info(f"No visitor data available: {e}")
            
            # Check conference registrations for additional company info
            conference_data = {}
            try:
                conference_response = self.supabase.table('conferences').select('*').execute()
                conference_data = {conf['userId']: conf for conf in conference_response.data}
                logger.info(f"Found {len(conference_data)} conference registrations")
            except Exception as e:
                logger.info(f"No conference data available: {e}")
            
            # Combine all user data
            users = []
            all_user_ids = set(user_details_by_id.keys()) | set(user_accounts_by_id.keys())
            
            for user_id in all_user_ids:
                user_detail = user_details_by_id.get(user_id, {})
                user_account = user_accounts_by_id.get(user_id, {})
                visitor_info = visitors_data.get(user_id, {})
                conference_info = conference_data.get(user_id, {})
                
                # Determine user type
                user_type = user_account.get('user_type', 'PARTICIPANT')
                if not user_type and visitor_info:
                    user_type = 'VISITOR'
                    
                # Get company info from various sources
                company_name = (
                    conference_info.get('companyName') or 
                    visitor_info.get('companyName') or 
                    ''
                )
                
                job_title = (
                    user_detail.get('position') or
                    conference_info.get('jobTitle') or 
                    visitor_info.get('jobTitle') or 
                    ''
                )
                
                user_data = {
                    'id': user_id,
                    'email': user_account.get('email', ''),
                    'firstName': user_detail.get('firstName', ''),
                    'lastName': user_detail.get('lastName', ''),
                    'middleName': user_detail.get('middleName', ''),
                    'userType': user_type,
                    'companyName': company_name,
                    'jobTitle': job_title,
                    'faceScannedUrl': user_detail.get('faceScannedUrl', ''),
                    'mobileNumber': user_account.get('mobileNumber', ''),
                    'status': user_account.get('status', 'ACTIVE')
                }
                
                # Only include users with at least basic info
                if user_data['firstName'] or user_data['lastName'] or user_data['email']:
                    users.append(user_data)
            
            logger.info(f"Retrieved {len(users)} users from combined user_details and user_accounts tables")
            
            if users:
                # Log sample user for debugging
                sample_user = users[0]
                logger.info(f"Sample user: {sample_user['firstName']} {sample_user['lastName']} ({sample_user['email']}) - Face URL: {'Yes' if sample_user['faceScannedUrl'] else 'No'}")
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting users with profiles: {e}")
            logger.info("Attempting fallback to attendance table for user data...")
            
            # Fallback: Get unique users from attendance table
            try:
                attendance_response = self.supabase.table('attendance').select('*').execute()
                
                # Get unique users from attendance records
                users_from_attendance = {}
                for record in attendance_response.data:
                    user_id = record['userId']
                    if user_id not in users_from_attendance:
                        users_from_attendance[user_id] = {
                            'id': user_id,
                            'email': record.get('email', ''),
                            'firstName': record.get('firstName', ''),
                            'lastName': record.get('lastName', ''),
                            'middleName': '',
                            'userType': record.get('userType', 'PARTICIPANT'),
                            'companyName': record.get('company', ''),
                            'jobTitle': record.get('jobTitle', ''),
                            'faceScannedUrl': '',  # Not available in attendance table
                        }
                
                users = list(users_from_attendance.values())
                logger.info(f"Fallback: Retrieved {len(users)} users from attendance table")
                return users
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return None
    
    def mark_attendance(self, user_id: str, user_data: Dict) -> Dict:
        """Mark attendance for a user via face recognition - only once per day"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Use Philippine timezone for consistent local time
                ph_now = self.get_ph_datetime()
                today = ph_now.date().isoformat()
                # Convert Philippine time to UTC for proper database storage
                utc_now = ph_now.astimezone(timezone.utc)
                current_time = utc_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + '+00'  # Store as UTC with timezone indicator
                
                # Check if user already marked attendance today
                existing_attendance = self.supabase.table('attendance').select('*').eq('userId', user_id).eq('scanDate', today).execute()
                
                if existing_attendance.data:
                    return {
                        'success': True,
                        'message': f"Welcome back! You already checked in today at {existing_attendance.data[0].get('scanTime')}",
                        'existing': True,
                        'attendance_time': existing_attendance.data[0].get('scanTime'),
                        'skip_display': True  # Don't show duplicate in attendance list
                    }
                
                # Insert new attendance record with face recognition marker
                attendance_data = {
                    'userId': user_id,
                    'firstName': user_data.get('firstName', ''),
                    'lastName': user_data.get('lastName', ''),
                    'email': user_data.get('email', ''),
                    'userType': user_data.get('userType', 'PARTICIPANT'),
                    'company': user_data.get('companyName', ''),
                    'jobTitle': user_data.get('jobTitle', ''),
                    'scanTime': current_time,
                    'scanDate': today,
                    'status': 'PRESENT'
                }
                
                response = self.supabase.table('attendance').insert(attendance_data).execute()
                
                logger.info(f"NEW attendance marked for user {user_id} - {user_data.get('firstName', '')} {user_data.get('lastName', '')} via face recognition (attempt {attempt + 1})")
                return {
                    'success': True,
                    'message': 'Welcome! Attendance marked successfully',
                    'existing': False,
                    'attendance_time': current_time,
                    'skip_display': False  # New attendance should be displayed
                }
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's an SSL/network error that should be retried
                if ("SSL" in error_msg or "timeout" in error_msg.lower() or "connection" in error_msg.lower()) and attempt < max_retries - 1:
                    logger.warning(f"Network/SSL error marking attendance on attempt {attempt + 1}/{max_retries}, retrying in 2 seconds... Error: {error_msg}")
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"Error marking attendance (final attempt): {error_msg}")
                    return {
                        'success': False,
                        'message': f'Error marking attendance: {error_msg}'
                    }
        
        # If we get here, all retries failed
        return {
            'success': False,
            'message': 'Failed to mark attendance - network connectivity issues'
        }
    
    def get_today_attendance(self) -> List[Dict]:
        """Get face recognition attendance records for today only"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Use Philippine timezone for consistent local date
                today = self.get_ph_date().isoformat()
                
                query = self.supabase.table('attendance').select('*').eq('scanDate', today)

                # Filter records with complete user data (face recognition typically has all fields)
                query = query.neq('firstName', '').neq('lastName', '').neq('email', '')
                
                response = query.order('scanTime', desc=True).execute()
                
                # Additional filtering to ensure only face recognition records
                face_recognition_records = []
                for record in response.data:
                    if (record.get('firstName') and 
                        record.get('lastName') and 
                        record.get('email') and
                        record.get('userId')):
                        # Convert scanTime to Philippine timezone for display
                        if record.get('scanTime'):
                            record['scanTime'] = self.convert_utc_to_ph_time(record['scanTime'])
                        face_recognition_records.append(record)
                
                logger.info(f"Retrieved {len(face_recognition_records)} face recognition attendance records for today (attempt {attempt + 1})")
                return face_recognition_records
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's an SSL/network error that should be retried
                if ("SSL" in error_msg or "timeout" in error_msg.lower() or "connection" in error_msg.lower()) and attempt < max_retries - 1:
                    logger.warning(f"Network/SSL error getting today's attendance on attempt {attempt + 1}/{max_retries}, retrying in 2 seconds... Error: {error_msg}")
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"Error getting today's face recognition attendance (final attempt): {error_msg}")
                    return []
        
        # If we get here, all retries failed
        logger.error("All retry attempts failed for get_today_attendance")
        return []
    
    def get_attendance_stats(self) -> Dict:
        """Get attendance statistics"""
        try:
            # Use Philippine timezone for consistent local date
            today = self.get_ph_date().isoformat()
            
            # Get today's attendance count
            today_response = self.supabase.table('attendance').select('count', count='exact').eq('scanDate', today).execute()
            today_count = today_response.count or 0
            
            # Get total registered users
            users_response = self.supabase.table('users').select('count', count='exact').execute()
            total_users = users_response.count or 0
            
            # Calculate attendance percentage
            attendance_percentage = (today_count / total_users * 100) if total_users > 0 else 0
            
            return {
                'success': True,
                'today_attendance': today_count,
                'total_users': total_users,
                'attendance_percentage': round(attendance_percentage, 1),
                'date': today
            }
            
        except Exception as e:
            logger.error(f"Error getting attendance stats: {e}")
            return {
                'success': False,
                'message': f'Error getting stats: {str(e)}'
            }
    
    def check_attendance_today(self, user_id: str) -> bool:
        """Check if a specific user has marked attendance today"""
        try:
            # Use Philippine timezone for consistent local date
            today = self.get_ph_date().isoformat()
            
            response = self.supabase.table('attendance').select('id').eq('userId', user_id).eq('scanDate', today).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking user attendance: {e}")
            return False
    
    def get_all_attendance(self, date_filter: str = None, user_type: str = None, status: str = None, company: str = None) -> Dict:
        """Get all attendance records with retry logic for SSL errors"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                query = self.supabase.table('attendance').select('*')
                
                # Apply filters
                if date_filter:
                    query = query.eq('scanDate', date_filter)
                if user_type:
                    query = query.eq('userType', user_type)
                if status:
                    query = query.eq('status', status)
                if company:
                    query = query.eq('company', company)
                
                # Order by most recent first
                query = query.order('scanTime', desc=True)
                
                response = query.execute()
                
                # Convert timestamps to Philippine timezone for display
                for record in response.data:
                    if record.get('scanTime'):
                        record['scanTime'] = self.convert_utc_to_ph_time(record['scanTime'])
                
                logger.info(f"Retrieved {len(response.data)} attendance records from database (attempt {attempt + 1})")
                return {
                    'success': True,
                    'data': response.data,
                    'count': len(response.data)
                }
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's an SSL/network error that should be retried
                if ("SSL" in error_msg or "timeout" in error_msg.lower() or "connection" in error_msg.lower()) and attempt < max_retries - 1:
                    logger.warning(f"Network/SSL error on attempt {attempt + 1}/{max_retries}, retrying in 2 seconds... Error: {error_msg}")
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"Error getting all attendance (final attempt): {error_msg}")
                    
                    # Check for permission errors and provide helpful message
                    if 'permission denied' in error_msg.lower() or '42501' in error_msg:
                        helpful_msg = (
                            "Permission denied accessing database. "
                            "Make sure you're using the SERVICE_ROLE key (not anon key) in your .env file. "
                            "Get it from Supabase Dashboard > Settings > API > service_role key."
                        )
                        logger.error(f"PERMISSION FIX NEEDED: {helpful_msg}")
                        return {
                            'success': False,
                            'message': helpful_msg,
                            'data': [],
                            'count': 0
                        }
                    elif 'unauthorized' in error_msg.lower() or '401' in error_msg:
                        helpful_msg = (
                            "Unauthorized access to database. "
                            "Check your SUPABASE_URL and SUPABASE_KEY in the .env file."
                        )
                        logger.error(f"AUTH FIX NEEDED: {helpful_msg}")
                        return {
                            'success': False,
                            'message': helpful_msg,
                            'data': [],
                            'count': 0
                        }
                    else:
                        return {
                            'success': False,
                            'message': f'Error getting attendance: {error_msg}',
                            'data': [],
                            'count': 0
                        }
        
        # If we get here, all retries failed
        return {
            'success': False,
            'message': 'All retry attempts failed - network connectivity issues',
            'data': [],
            'count': 0
        }
    
    def get_face_recognition_attendance(self, date_filter: str = None, user_type: str = None, status: str = None, company: str = None) -> Dict:
        """Get only attendance records created through face recognition"""
        try:
            query = self.supabase.table('attendance').select('*')
            
            # Filter only records created through face recognition
            # Use complete user data as indicator (face recognition records have full data)
            query = query.neq('firstName', '').neq('lastName', '').neq('email', '')
            
            # Apply additional filters
            if date_filter:
                query = query.eq('scanDate', date_filter)
            if user_type:
                query = query.eq('userType', user_type)
            if status:
                query = query.eq('status', status)
            if company:
                query = query.eq('company', company)
            
            # Order by most recent first
            query = query.order('scanTime', desc=True)
            
            response = query.execute()
            
            # Filter out any records that don't look like they came from face recognition
            face_recognition_records = []
            for record in response.data:
                # Only include records that have the face recognition characteristics:
                # - Complete user information
                # - Recent creation (not old manual entries)
                if (record.get('firstName') and 
                    record.get('lastName') and 
                    record.get('email') and
                    record.get('userId')):
                    face_recognition_records.append(record)
            
            logger.info(f"Retrieved {len(face_recognition_records)} face recognition attendance records")
            
            return {
                'success': True,
                'data': face_recognition_records,
                'count': len(face_recognition_records)
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting face recognition attendance: {error_msg}")
            
            return {
                'success': False,
                'message': f'Error getting face recognition attendance: {error_msg}',
                'data': [],
                'count': 0
            }
    

