import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import os
import pickle
import logging
from typing import List, Dict, Optional, Tuple
import requests
from io import BytesIO
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArcFaceService:
    def __init__(self):
        self.app = None
        self.face_database = {}
        self.embeddings_file = 'face_embeddings.pkl'
        self.similarity_threshold = 0.5
        
        self.initialize_model()
        
    def initialize_model(self):
        """Initialize the ArcFace model"""
        try:
            self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("ArcFace model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ArcFace model: {e}")
            raise e
    
    def load_face_database(self):
        """Load existing face database from file"""
        if os.path.exists(self.embeddings_file):
            try:
                with open(self.embeddings_file, 'rb') as f:
                    self.face_database = pickle.load(f)
                logger.info(f"Loaded {len(self.face_database)} faces from database")
            except Exception as e:
                logger.error(f"Error loading face database: {e}")
                self.face_database = {}
        else:
            self.face_database = {}
    
    def save_face_database(self):
        """Save face database to file"""
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.face_database, f)
            logger.info(f"Saved {len(self.face_database)} faces to database")
        except Exception as e:
            logger.error(f"Error saving face database: {e}")
    
    def download_image(self, url: str) -> Optional[np.ndarray]:
        """Download image from URL and convert to OpenCV format"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                # Convert PIL image to OpenCV format
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                return opencv_image
            else:
                logger.error(f"Failed to download image from {url}, status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def extract_face_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face embedding from image using ArcFace"""
        try:
            faces = self.app.get(image)
            if len(faces) > 0:
                # Get the face with highest confidence
                face = max(faces, key=lambda x: x.det_score)
                return face.normed_embedding
            else:
                logger.warning("No face detected in image")
                return None
        except Exception as e:
            logger.error(f"Error extracting face embedding: {e}")
            return None
    
    def register_user_face(self, user_id: str, user_data: Dict, image_url: str) -> bool:
        """Register a user's face in the database"""
        try:
            # Skip processing for placeholder/mock images
            if 'placeholder' in image_url.lower() or 'via.placeholder' in image_url.lower():
                logger.info(f"Skipping placeholder image for user {user_id}")
                # Create a mock embedding for development
                mock_embedding = np.random.rand(512).astype(np.float32)
                self.face_database[user_id] = {
                    'embedding': mock_embedding,
                    'user_data': user_data
                }
                logger.info(f"Registered mock face for user {user_id}")
                return True
            
            # Download and process image
            image = self.download_image(image_url)
            if image is None:
                return False
            
            # Extract face embedding
            embedding = self.extract_face_embedding(image)
            if embedding is None:
                return False
            
            # Store in database
            self.face_database[user_id] = {
                'embedding': embedding,
                'user_data': user_data
            }
            
            logger.info(f"Registered face for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering user face: {e}")
            return False
    
    def register_multiple_faces(self, users_data: List[Dict]) -> int:
        """Register multiple users' faces"""
        success_count = 0
        
        for user in users_data:
            if user.get('faceScannedUrl'):
                success = self.register_user_face(
                    user['id'], 
                    user, 
                    user['faceScannedUrl']
                )
                if success:
                    success_count += 1
        
        self.save_face_database()
        logger.info(f"Successfully registered {success_count} out of {len(users_data)} users")
        return success_count
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Normalize embeddings
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def recognize_face_from_image(self, image: np.ndarray) -> Optional[Dict]:
        """Recognize face from image"""
        try:
            # Extract embedding from input image
            query_embedding = self.extract_face_embedding(image)
            if query_embedding is None:
                return None
            
            best_match = None
            best_similarity = 0.0
            
            # Compare with all registered faces
            for user_id, data in self.face_database.items():
                stored_embedding = data['embedding']
                similarity = self.calculate_similarity(query_embedding, stored_embedding)
                
                if similarity > best_similarity and similarity > self.similarity_threshold:
                    best_similarity = similarity
                    best_match = {
                        'user_id': user_id,
                        'user_data': data['user_data'],
                        'similarity': similarity
                    }
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error recognizing face: {e}")
            return None
    
    def recognize_face_from_base64(self, base64_image: str) -> Optional[Dict]:
        """Recognize face from base64 encoded image"""
        try:
            # For development with mock data, return a random recognition
            if len(self.face_database) > 0:
                # Check if we have any real face embeddings or just mock ones
                has_real_embeddings = any(
                    not np.array_equal(data['embedding'], np.random.rand(512).astype(np.float32))
                    for data in self.face_database.values()
                )
                
                if not has_real_embeddings:
                    # Return a random user for demo purposes with mock data
                    import random
                    user_id = random.choice(list(self.face_database.keys()))
                    data = self.face_database[user_id]
                    logger.info(f"Mock recognition: returning user {user_id}")
                    return {
                        'user_id': user_id,
                        'user_data': data['user_data'],
                        'similarity': 0.85  # Mock high similarity
                    }
            
            # Decode base64 image
            import base64
            image_data = base64.b64decode(base64_image.split(',')[1] if ',' in base64_image else base64_image)
            image = Image.open(BytesIO(image_data))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            return self.recognize_face_from_image(opencv_image)
            
        except Exception as e:
            logger.error(f"Error recognizing face from base64: {e}")
            return None
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the face database"""
        return {
            'total_faces': len(self.face_database),
            'threshold': self.similarity_threshold
        }
    
    def update_threshold(self, new_threshold: float) -> bool:
        """Update similarity threshold"""
        try:
            if 0.0 <= new_threshold <= 1.0:
                self.similarity_threshold = new_threshold
                logger.info(f"Updated similarity threshold to {new_threshold}")
                return True
            else:
                logger.error("Threshold must be between 0.0 and 1.0")
                return False
        except Exception as e:
            logger.error(f"Error updating threshold: {e}")
            return False
