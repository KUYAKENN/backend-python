#!/usr/bin/env python3
"""
Test script for the new face recognition endpoints
"""

import requests
import base64
import json
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Test server configuration
BASE_URL = "http://localhost:5000"

def create_test_image():
    """Create a simple test image (solid color rectangle)"""
    from PIL import Image
    import io
    
    # Create a simple 200x200 image
    img = Image.new('RGB', (200, 200), color='blue')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/jpeg;base64,{img_str}"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a specific endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"\n{'='*60}")
        print(f"Testing {method} {endpoint}")
        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Response: {response.text}")
            
        return response.status_code, response.json() if response.headers.get('content-type') == 'application/json' else response.text
        
    except Exception as e:
        print(f"Error testing {endpoint}: {e}")
        return None, None

def main():
    """Run all tests"""
    print("Testing Face Recognition API Endpoints")
    print("="*60)
    
    # Test basic connectivity
    test_endpoint("/health")
    test_endpoint("/")
    
    # Test new face endpoints
    test_image = create_test_image()
    
    # Test facial landmark extraction
    test_endpoint("/extract-landmarks", "POST", {"image": test_image})
    
    # Test face enrollment
    test_endpoint("/enroll", "POST", {
        "user_id": "test_user_123",
        "image": test_image,
        "user_data": {
            "firstName": "Test",
            "lastName": "User",
            "email": "test@example.com"
        }
    })
    
    # Test listing faces
    test_endpoint("/faces")
    
    # Test face recognition with enrolled face
    test_endpoint("/recognize", "POST", {"image": test_image})
    
    # Test removing face
    test_endpoint("/faces/test_user_123", "DELETE")
    
    # Test listing faces again (should be empty)
    test_endpoint("/faces")
    
    print(f"\n{'='*60}")
    print("All tests completed!")

if __name__ == "__main__":
    main()
