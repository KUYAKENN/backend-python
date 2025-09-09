from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
from datetime import date, datetime
import logging
import threading
import time
import os
import pandas as pd
import base64

from .arcface_service import ArcFaceService
from .supabase_service import SupabaseService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceRecognitionApp:
    def __init__(self):
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # Configure CORS to allow all origins and bypass CORS restrictions
        CORS(self.app, 
             origins="*",  # Allow all origins
             allow_headers=["*"],  # Allow all headers
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow all common methods
             supports_credentials=True)
        
        # Initialize services
        self.arcface_service = ArcFaceService()
        self.supabase_service = SupabaseService()
        
        # Recognition cooldown tracking
        self.last_recognition = {}
        self.RECOGNITION_COOLDOWN = 3  # seconds between recognitions for same user
        
        # Auto-reload configuration
        self.auto_reload_manager = AutoReloadManager(
            self.arcface_service, 
            self.supabase_service
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all Flask routes"""
        
        # Add manual CORS headers for all responses
        @self.app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
        
        # Handle preflight OPTIONS requests
        @self.app.route('/<path:path>', methods=['OPTIONS'])
        def handle_options(path):
            response = jsonify({'status': 'ok'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'message': 'ArcFace Recognition Service is running'
            })

        @self.app.route('/auto-reload/start', methods=['POST'])
        def start_auto_reload():
            """Start automatic monitoring for new user registrations"""
            try:
                self.auto_reload_manager.start_monitoring()
                return jsonify({
                    'success': True,
                    'message': 'Auto-reload monitoring started',
                    'check_interval': self.auto_reload_manager.check_interval
                })
            except Exception as e:
                logger.error(f"Error starting auto-reload: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error starting auto-reload: {str(e)}'
                }), 500

        @self.app.route('/auto-reload/stop', methods=['POST'])
        def stop_auto_reload():
            """Stop automatic monitoring"""
            try:
                self.auto_reload_manager.stop_monitoring()
                return jsonify({
                    'success': True,
                    'message': 'Auto-reload monitoring stopped'
                })
            except Exception as e:
                logger.error(f"Error stopping auto-reload: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error stopping auto-reload: {str(e)}'
                }), 500

        @self.app.route('/auto-reload/status', methods=['GET'])
        def auto_reload_status():
            """Get auto-reload status"""
            return jsonify({
                'success': True,
                'auto_reload_enabled': self.auto_reload_manager.auto_reload_enabled,
                'check_interval': self.auto_reload_manager.check_interval,
                'known_user_count': self.auto_reload_manager.known_user_count
            })

        @self.app.route('/initialize', methods=['POST'])
        def initialize_system():
            """Initialize the face recognition system with user data"""
            try:
                # Load face database
                self.arcface_service.load_face_database()
                
                # Get all users from Supabase
                users = self.supabase_service.get_all_users_with_profiles()
                
                if not users:
                    return jsonify({
                        'success': False,
                        'message': 'No users found in database'
                    }), 404
                
                # Register faces
                success_count = self.arcface_service.register_multiple_faces(users)
                
                # Update auto-reload manager
                self.auto_reload_manager.known_user_count = len(users)
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully registered {success_count} faces',
                    'total_users': len(users),
                    'registered_faces': success_count
                })
                
            except Exception as e:
                logger.error(f"Error initializing system: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error initializing system: {str(e)}'
                }), 500

        @self.app.route('/recognize', methods=['POST'])
        def recognize_face():
            """Recognize face from uploaded image and mark attendance"""
            try:
                data = request.get_json()
                
                if not data or 'image' not in data:
                    return jsonify({
                        'success': False,
                        'message': 'No image data provided'
                    }), 400
                
                # Get base64 image
                base64_image = data['image']
                
                # Recognize face
                result = self.arcface_service.recognize_face_from_base64(base64_image)
                
                if result:
                    user_data = result['user_data']
                    user_id = user_data['id']
                    
                    # Check cooldown to prevent spam recognition
                    current_time = time.time()
                    if user_id in self.last_recognition:
                        time_diff = current_time - self.last_recognition[user_id]
                        if time_diff < self.RECOGNITION_COOLDOWN:
                            return jsonify({
                                'success': True,
                                'recognized': True,
                                'message': f'Please wait {self.RECOGNITION_COOLDOWN - int(time_diff)} seconds before next recognition',
                                'cooldown_remaining': self.RECOGNITION_COOLDOWN - time_diff
                            })
                    
                    # Update last recognition time
                    self.last_recognition[user_id] = current_time
                    
                    # Mark attendance
                    attendance_result = self.supabase_service.mark_attendance(user_id, user_data)
                    
                    # Check if this is a duplicate entry that shouldn't be displayed
                    if attendance_result.get('skip_display', False):
                        # Return recognition success but with duplicate message
                        return jsonify({
                            'success': True,
                            'recognized': True,
                            'duplicate_entry': True,
                            'message': attendance_result.get('message', 'Already checked in today'),
                            'user': {
                                'id': user_data['id'],
                                'firstName': user_data['firstName'],
                                'lastName': user_data['lastName'],
                                'middleName': user_data.get('middleName', ''),
                                'userType': user_data['userType'],
                                'email': user_data['email'],
                                'companyName': user_data.get('companyName', ''),
                                'jobTitle': user_data.get('jobTitle', '')
                            },
                            'similarity': result['similarity'],
                            'attendance': attendance_result
                        })
                    
                    response_data = {
                        'success': True,
                        'recognized': True,
                        'duplicate_entry': False,
                        'user': {
                            'id': user_data['id'],
                            'firstName': user_data['firstName'],
                            'lastName': user_data['lastName'],
                            'middleName': user_data.get('middleName', ''),
                            'userType': user_data['userType'],
                            'email': user_data['email'],
                            'companyName': user_data.get('companyName', ''),
                            'jobTitle': user_data.get('jobTitle', '')
                        },
                        'similarity': result['similarity'],
                        'attendance': attendance_result
                    }
                    
                    return jsonify(response_data)
                else:
                    return jsonify({
                        'success': True,
                        'recognized': False,
                        'message': 'No matching face found - Access Denied'
                    })
                    
            except Exception as e:
                logger.error(f"Error recognizing face: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error recognizing face: {str(e)}'
                }), 500

        @self.app.route('/attendance', methods=['GET'])
        def get_attendance():
            """Get all attendance records for today"""
            try:
                attendance_records = self.supabase_service.get_today_attendance()
                return jsonify({
                    'success': True,
                    'attendance': attendance_records
                })
            except Exception as e:
                logger.error(f"Error getting today's attendance: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error getting attendance: {str(e)}'
                }), 500

        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get system statistics"""
            try:
                stats = self.arcface_service.get_database_stats()
                
                # Get total users from database
                try:
                    all_users = self.supabase_service.get_all_users_with_profiles()
                    total_users = len(all_users) if all_users else 0
                except Exception as e:
                    logger.warning(f"Could not get user count from database: {e}")
                    total_users = 0
                
                # Enhanced stats with both face count and user count
                enhanced_stats = {
                    'total_users': total_users,
                    'total_faces': stats['total_faces'],
                    'users_with_faces': stats['total_faces'],
                    'threshold': stats['threshold']
                }
                
                return jsonify({
                    'success': True,
                    'stats': enhanced_stats
                })
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error getting stats: {str(e)}'
                }), 500

        @self.app.route('/threshold', methods=['POST'])
        def update_threshold():
            """Update similarity threshold"""
            try:
                data = request.get_json()
                
                if not data or 'threshold' not in data:
                    return jsonify({
                        'success': False,
                        'message': 'Threshold value is required'
                    }), 400
                
                threshold = float(data['threshold'])
                success = self.arcface_service.update_threshold(threshold)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Threshold updated to {threshold}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid threshold value. Must be between 0.0 and 1.0'
                    }), 400
                    
            except Exception as e:
                logger.error(f"Error updating threshold: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error updating threshold: {str(e)}'
                }), 500

        @self.app.route('/refresh', methods=['POST'])
        def refresh_database():
            """Refresh the face database with latest user data"""
            try:
                # Get updated users from Supabase
                users = self.supabase_service.get_all_users_with_profiles()
                
                if not users:
                    return jsonify({
                        'success': False,
                        'message': 'No users found in database'
                    }), 404
                
                # Clear existing database and re-register faces
                self.arcface_service.face_database.clear()
                success_count = self.arcface_service.register_multiple_faces(users)
                
                return jsonify({
                    'success': True,
                    'message': f'Database refreshed. Registered {success_count} faces',
                    'total_users': len(users),
                    'registered_faces': success_count
                })
                
            except Exception as e:
                logger.error(f"Error refreshing database: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error refreshing database: {str(e)}'
                }), 500

        @self.app.route('/debug', methods=['GET'])
        def debug_database():
            """Debug endpoint to test database connectivity and configuration"""
            try:
                # Get detailed test results from supabase service
                test_results = self.supabase_service.test_database_access()
                
                return jsonify({
                    'status': 'success',
                    'test_results': test_results
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Debug failed: {str(e)}'
                }), 500

        # ===== ATTENDANCE ENDPOINTS =====

        @self.app.route('/attendance/today', methods=['GET'])
        def get_today_attendance():
            """Get all attendance records for today"""
            try:
                attendance_records = self.supabase_service.get_today_attendance()
                attendance_stats = self.supabase_service.get_attendance_stats()
                
                return jsonify({
                    'success': True,
                    'attendance_records': attendance_records,
                    'stats': attendance_stats,
                    'total_today': len(attendance_records)
                })
                
            except Exception as e:
                logger.error(f"Error getting today's attendance: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error getting attendance: {str(e)}'
                }), 500

        @self.app.route('/attendance/stats', methods=['GET'])
        def get_attendance_stats():
            """Get attendance statistics"""
            try:
                stats = self.supabase_service.get_attendance_stats()
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"Error getting attendance stats: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error getting attendance stats: {str(e)}'
                }), 500

        @self.app.route('/attendance/check/<user_id>', methods=['GET'])
        def check_user_attendance(user_id):
            """Check if specific user has marked attendance today"""
            try:
                has_attended = self.supabase_service.check_attendance_today(user_id)
                
                return jsonify({
                    'success': True,
                    'user_id': user_id,
                    'has_attended_today': has_attended,
                    'date': date.today().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error checking user attendance: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error checking attendance: {str(e)}'
                }), 500

        @self.app.route('/attendance/export', methods=['GET'])
        def export_attendance():
            """Export today's attendance to Excel"""
            try:
                # Get today's attendance
                attendance_records = self.supabase_service.get_today_attendance()
                
                if not attendance_records:
                    return jsonify({
                        'success': False,
                        'message': 'No attendance records found for today'
                    }), 404
                
                # Create DataFrame
                df = pd.DataFrame(attendance_records)
                
                # Format columns for export
                column_mapping = {
                    'userId': 'User ID',
                    'firstName': 'First Name', 
                    'lastName': 'Last Name',
                    'email': 'Email',
                    'userType': 'User Type',
                    'company': 'Company',
                    'jobTitle': 'Job Title',
                    'scanTime': 'Time In',
                    'scanDate': 'Date',
                    'status': 'Status'
                }
                
                # Select and rename columns that exist
                columns_to_include = [col for col in column_mapping.keys() if col in df.columns]
                df_export = df[columns_to_include].copy()
                df_export = df_export.rename(columns=column_mapping)
                
                # Format time column
                if 'Time In' in df_export.columns:
                    df_export['Time In'] = pd.to_datetime(df_export['Time In']).dt.strftime('%I:%M:%S %p')
                
                # Create Excel file in memory
                output = BytesIO()
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Daily Attendance', index=False)
                    
                    # Format the worksheet
                    workbook = writer.book
                    worksheet = writer.sheets['Daily Attendance']
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                output.seek(0)
                
                # Generate filename
                today_str = date.today().strftime('%Y-%m-%d')
                filename = f'BEACON_2025_Attendance_{today_str}.xlsx'
                
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=filename
                )
                
            except Exception as e:
                logger.error(f"Error exporting attendance: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error exporting attendance: {str(e)}'
                }), 500

        @self.app.route('/api/attendance', methods=['GET'])
        def get_all_attendance():
            """Get all attendance records from attendance table"""
            try:
                # Get query parameters for filtering
                date_filter = request.args.get('date')
                user_type = request.args.get('userType')
                status = request.args.get('status')
                company = request.args.get('company')
                
                # Get all attendance data from supabase attendance table
                attendance_records = self.supabase_service.get_all_attendance(
                    date_filter=date_filter,
                    user_type=user_type,
                    status=status,
                    company=company
                )
                
                return jsonify(attendance_records)
                
            except Exception as e:
                logger.error(f"Error fetching attendance records: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error fetching attendance: {str(e)}'
                }), 500

    def initialize_on_startup(self):
        """Initialize system on startup"""
        try:
            logger.info("Starting ArcFace Recognition Service...")
            
            # Load existing face database
            self.arcface_service.load_face_database()
            
            # If no faces in database, try to load from Supabase
            if len(self.arcface_service.face_database) == 0:
                logger.info("No faces in local database, loading from Supabase...")
                users = self.supabase_service.get_all_users_with_profiles()
                if users:
                    success_count = self.arcface_service.register_multiple_faces(users)
                    self.auto_reload_manager.known_user_count = len(users)
                    logger.info(f"Registered {success_count} faces from Supabase")
            
            logger.info(f"System ready with {len(self.arcface_service.face_database)} registered faces")
            
            # Start auto-reload monitoring
            self.auto_reload_manager.start_monitoring()
            logger.info("🔄 Auto-reload monitoring enabled - system will detect new registrations automatically")
            
        except Exception as e:
            logger.error(f"Error during startup: {e}")

    def get_flask_app(self):
        """Get the Flask app instance"""
        return self.app


class AutoReloadManager:
    def __init__(self, arcface_service, supabase_service):
        self.arcface_service = arcface_service
        self.supabase_service = supabase_service
        self.known_user_count = 0
        self.auto_reload_enabled = False
        self.check_interval = 60  # Check every 60 seconds
        self.monitoring_thread = None
        
    def start_monitoring(self):
        """Start background monitoring for new users"""
        if not self.auto_reload_enabled:
            self.auto_reload_enabled = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("🔄 Auto-reload monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.auto_reload_enabled = False
        logger.info("⏹️ Auto-reload monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.auto_reload_enabled:
            try:
                # Check for new users
                users = self.supabase_service.get_all_users_with_profiles()
                current_count = len(users) if users else 0
                
                if self.known_user_count == 0:
                    # First time initialization
                    self.known_user_count = current_count
                    logger.info(f"📊 Initial user count: {current_count}")
                elif current_count > self.known_user_count:
                    # New users detected, reload face database
                    logger.info(f"🆕 New users detected! Count changed from {self.known_user_count} to {current_count}")
                    success_count = self.arcface_service.register_multiple_faces(users)
                    self.known_user_count = current_count
                    logger.info(f"✅ Reloaded face database with {success_count} faces")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in auto-reload monitoring: {e}")
                time.sleep(self.check_interval)


# Create the Flask app instance
face_recognition_app = FaceRecognitionApp()
app = face_recognition_app.get_flask_app()

# Initialize on import
face_recognition_app.initialize_on_startup()
