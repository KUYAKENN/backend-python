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
        try:
            # Use Philippine timezone for consistent local time
            ph_now = self.get_ph_datetime()
            today = ph_now.date().isoformat()
            # Store time as Philippine time WITHOUT timezone info to avoid Supabase conversion
            current_time = ph_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Remove microseconds to match DB format
            
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
            
            logger.info(f"NEW attendance marked for user {user_id} - {user_data.get('firstName', '')} {user_data.get('lastName', '')} via face recognition")
            return {
                'success': True,
                'message': 'Welcome! Attendance marked successfully',
                'existing': False,
                'attendance_time': current_time,
                'skip_display': False  # New attendance should be displayed
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error marking attendance: {error_msg}")
            return {
                'success': False,
                'message': f'Error marking attendance: {error_msg}'
            }
    
    def get_today_attendance(self) -> List[Dict]:
        """Get face recognition attendance records for today only"""
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
            
            logger.info(f"Retrieved {len(face_recognition_records)} face recognition attendance records for today")
            return face_recognition_records
            
        except Exception as e:
            logger.error(f"Error getting today's face recognition attendance: {e}")
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
        """Get all attendance records with optional filtering"""
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
            
            return {
                'success': True,
                'data': response.data,
                'count': len(response.data)
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting all attendance: {error_msg}")
            
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
    
    def get_all_attendance(self, date_filter=None, user_type=None, status=None, company=None) -> List[Dict]:
        """Get all attendance records from attendance table with optional filtering"""
        try:
            # Start with base query
            query = self.supabase.table('attendance').select('*')
            
            # Apply filters if provided
            if date_filter:
                query = query.eq('scanDate', date_filter)
            
            if user_type:
                query = query.eq('userType', user_type)
                
            if status:
                query = query.eq('status', status)
                
            if company:
                query = query.eq('companyName', company)
            
            # Order by most recent first
            response = query.order('scanDate', desc=True).order('scanTime', desc=True).execute()
            
            logger.info(f"Retrieved {len(response.data)} attendance records from database")
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting all attendance records: {e}")
            return []
