#!/usr/bin/env python3
"""
Face Database Scanner and Processor
This script scans existing face images from your database and processes them for recognition.
"""

import os
import sys
import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'face_scan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class FaceDatabaseScanner:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        
    def check_server_status(self):
        """Check if the face recognition server is running"""
        try:
            logger.info("🔍 Checking server status...")
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ Server is running and accessible")
                return True
            else:
                logger.error(f"❌ Server returned status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to server. Please start the Flask application first.")
            logger.info("💡 Run: python src/flask_app.py")
            return False
        except requests.exceptions.Timeout:
            logger.error("❌ Server is not responding (timeout)")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking server: {e}")
            return False
    
    def check_database_setup(self):
        """Verify database tables exist"""
        try:
            logger.info("📊 Checking database setup...")
            response = requests.get(f"{self.base_url}/face-status", timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Database tables are accessible")
                return True
            else:
                logger.error("❌ Database tables not found")
                logger.info("💡 Please run the SQL setup first:")
                logger.info("   1. Open Supabase dashboard")
                logger.info("   2. Go to SQL Editor")
                logger.info("   3. Copy/paste contents of QUICK_SETUP.sql")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database check failed: {e}")
            return False
    
    def get_current_status(self):
        """Get current face enrollment status"""
        try:
            logger.info("📈 Getting current enrollment status...")
            response = requests.get(f"{self.base_url}/face-status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('data', [])
                
                # Count by status
                status_counts = {
                    'enrolled': 0,
                    'pending': 0,
                    'no_image': 0,
                    'total': len(users)
                }
                
                for user in users:
                    status = user.get('enrollment_status', 'no_image')
                    if status in status_counts:
                        status_counts[status] += 1
                
                logger.info("📊 Current Status:")
                logger.info(f"   📸 Total Users: {status_counts['total']}")
                logger.info(f"   ✅ Already Enrolled: {status_counts['enrolled']}")
                logger.info(f"   ⏳ Pending (Have Images): {status_counts['pending']}")
                logger.info(f"   ❌ No Images: {status_counts['no_image']}")
                
                return status_counts
                
        except Exception as e:
            logger.error(f"❌ Error getting status: {e}")
            return {}
    
    def scan_and_process_faces(self):
        """Scan and process all pending face images"""
        try:
            logger.info("🔄 Starting face scanning and processing...")
            logger.info("⚠️  This may take several minutes depending on the number of images...")
            
            # Make the sync request with extended timeout
            response = requests.post(
                f"{self.base_url}/sync-faces-from-db", 
                timeout=600,  # 10 minutes timeout
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Face scanning completed!")
                
                # Process results
                if 'results' in result:
                    successful = [r for r in result['results'] if r['status'] == 'success']
                    failed = [r for r in result['results'] if r['status'] == 'failed']
                    
                    logger.info("📊 Processing Results:")
                    logger.info(f"   ✅ Successfully processed: {len(successful)} faces")
                    logger.info(f"   ❌ Failed to process: {len(failed)} faces")
                    
                    # Show success details
                    if successful:
                        logger.info("\n✅ Successfully Enrolled:")
                        for success in successful[:10]:  # Show first 10
                            user_name = success.get('user_name', 'Unknown')
                            confidence = success.get('confidence', 0)
                            logger.info(f"   - {user_name} (confidence: {confidence:.3f})")
                        
                        if len(successful) > 10:
                            logger.info(f"   ... and {len(successful) - 10} more")
                    
                    # Show failure details
                    if failed:
                        logger.info("\n❌ Failed to Process:")
                        for failure in failed[:10]:  # Show first 10
                            user_name = failure.get('user_name', 'Unknown')
                            reason = failure.get('message', 'Unknown error')
                            logger.info(f"   - {user_name}: {reason}")
                        
                        if len(failed) > 10:
                            logger.info(f"   ... and {len(failed) - 10} more")
                
                return True
                
            else:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                
                logger.error(f"❌ Face scanning failed: {error_msg}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Request timed out - processing may still be running")
            logger.info("💡 Check server logs or try again later")
            return False
        except Exception as e:
            logger.error(f"❌ Error during face scanning: {e}")
            return False
    
    def verify_results(self):
        """Verify the face processing results"""
        try:
            logger.info("🧪 Verifying processing results...")
            
            # Get updated status
            final_status = self.get_current_status()
            
            # Get face count
            response = requests.get(f"{self.base_url}/faces", timeout=10)
            if response.status_code == 200:
                faces_data = response.json()
                face_count = faces_data.get('total_count', 0)
                logger.info(f"✅ Total enrolled faces in system: {face_count}")
                
                if face_count > 0:
                    logger.info("🎉 Face recognition system is ready for use!")
                    return True
                else:
                    logger.warning("⚠️  No faces were successfully enrolled")
                    return False
            else:
                logger.error("❌ Could not verify face enrollment")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verifying results: {e}")
            return False
    
    def run_complete_scan(self):
        """Run the complete face scanning process"""
        logger.info("="*70)
        logger.info("🎯 FACE DATABASE SCANNER STARTED")
        logger.info("="*70)
        
        # Step 1: Check server
        if not self.check_server_status():
            logger.error("❌ Cannot proceed without running server")
            return False
        
        # Step 2: Check database
        if not self.check_database_setup():
            logger.error("❌ Cannot proceed without database setup")
            return False
        
        # Step 3: Show initial status
        initial_status = self.get_current_status()
        if not initial_status:
            logger.error("❌ Cannot get current status")
            return False
        
        # Check if there's anything to process
        if initial_status.get('pending', 0) == 0:
            logger.info("ℹ️  No pending images found to process")
            logger.info("✅ All users are already enrolled or don't have face images")
            return True
        
        # Step 4: Process faces
        logger.info(f"\n🚀 Processing {initial_status['pending']} pending face images...")
        if not self.scan_and_process_faces():
            logger.error("❌ Face processing failed")
            return False
        
        # Step 5: Verify results
        if not self.verify_results():
            logger.warning("⚠️  Results verification failed")
        
        # Success
        logger.info("="*70)
        logger.info("🎉 FACE SCANNING COMPLETE!")
        logger.info("="*70)
        logger.info("✅ Your existing face images have been processed")
        logger.info("✅ Face recognition system is ready")
        logger.info("✅ Users can now be recognized via the /recognize endpoint")
        
        return True

def main():
    """Main function"""
    print("🎯 Face Database Scanner")
    print("=" * 50)
    
    # Check if Flask app exists
    if not os.path.exists('src/flask_app.py'):
        print("❌ Flask application not found at src/flask_app.py")
        print("Please ensure you have the complete face recognition system files.")
        return False
    
    # Check if database schema file exists
    if not os.path.exists('QUICK_SETUP.sql'):
        print("❌ Database schema file 'QUICK_SETUP.sql' not found")
        print("Please ensure you have the database setup file.")
        return False
    
    # Ask user to confirm server is running
    print("\n⚠️  IMPORTANT: Make sure your Flask server is running!")
    print("   Run this in another terminal: python src/flask_app.py")
    print("\n⚠️  Also ensure you've run the database setup (QUICK_SETUP.sql)")
    print("   Copy/paste the SQL into your Supabase dashboard")
    
    user_input = input("\nPress Enter to continue (or 'q' to quit): ").strip().lower()
    if user_input in ['q', 'quit', 'exit']:
        print("👋 Goodbye!")
        return True
    
    # Run the scanner
    scanner = FaceDatabaseScanner()
    return scanner.run_complete_scan()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Scanner completed successfully!")
    else:
        print("\n❌ Scanner failed. Check the logs above.")
    
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
