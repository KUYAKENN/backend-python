# Face Recognition Backend Service

This is a Flask-based face recognition service using ArcFace for facial recognition and Supabase for data storage.

## Features

- **Face Recognition**: Real-time face recognition using ArcFace models
- **Face Enrollment**: Register new faces with facial landmarks extraction
- **Attendance Tracking**: Automatic attendance marking upon face recognition
- **Facial Analytics**: Extract age, gender, and facial landmarks
- **RESTful API**: Complete set of endpoints for face management

## Start Service

### Step 1 - Create environment

Install requirements:

```bash
pip install -r requirements.txt
```

### Step 2 - Set up environment variables

Create a `.env` file with your Supabase credentials:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Step 3 - Start service locally

1. Run service with main method:

```bash
python main.py
```

2. The service will be available at http://localhost:5000

## API Endpoints

### Core Recognition
- `POST /recognize` - Recognize face from image and mark attendance
- `GET /health` - Health check endpoint

### Face Enrollment & Management
- `POST /enroll` - Enroll a new face for recognition
- `GET /faces` - List all enrolled faces
- `DELETE /faces/{user_id}` - Remove a specific user's face

### Facial Analysis
- `POST /extract-landmarks` - Extract facial landmarks and information from image

### Attendance Management
- `GET /attendance` - Get today's attendance records
- `GET /attendance/today` - Get detailed today's attendance
- `GET /attendance/stats` - Get attendance statistics
- `GET /attendance/check/{user_id}` - Check specific user's attendance

### System Management
- `POST /initialize` - Initialize face database from Supabase users
- `POST /refresh` - Refresh face database
- `GET /stats` - Get system statistics
- `POST /threshold` - Update recognition threshold

## Usage Examples

### Enroll a new face:
```bash
curl -X POST http://localhost:5000/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "user_data": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com"
    }
  }'
```

### Extract facial landmarks:
```bash
curl -X POST http://localhost:5000/extract-landmarks \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
  }'
```

### Recognize face:
```bash
curl -X POST http://localhost:5000/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
  }'
```

## Testing

Run the test script to verify all endpoints:

```bash
python test_face_endpoints.py
```

## Technical Details

- **Face Recognition**: Uses InsightFace ArcFace model for high-accuracy face recognition
- **Facial Landmarks**: Extracts 5-point facial landmarks (eyes, nose, mouth corners)
- **Database**: Stores face embeddings locally in pickle format, user data in Supabase
- **CORS**: Configured for cross-origin requests
- **Image Processing**: Supports base64 encoded images
