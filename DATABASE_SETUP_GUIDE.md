# Face Recognition Database Setup Guide

## Overview
This guide provides SQL queries to add face recognition capabilities to your existing Supabase database.

## Choose Your Schema

### Option 1: With pgvector Extension (Recommended)
Use `face_embeddings_schema.sql` if your Supabase instance has the pgvector extension enabled.
- More efficient vector operations
- Better performance for similarity searches
- Native vector indexing support

### Option 2: Without pgvector Extension  
Use `face_embeddings_schema_jsonb.sql` if pgvector is not available.
- Uses JSONB to store embeddings as arrays
- Includes custom cosine similarity function
- Works with any PostgreSQL instance

## Quick Start Commands

### 1. Run the Schema
```sql
-- Copy and paste the contents of either schema file into your Supabase SQL editor
-- Execute all commands in order
```

### 2. Verify Installation
```sql
-- Check if tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'face_%';

-- Should return:
-- face_embeddings
-- face_landmarks  
-- face_recognition_log
-- face_enrollment_log (if using JSONB version)
```

### 3. Check Users Ready for Enrollment
```sql
SELECT id, firstName, lastName, faceScannedUrl 
FROM user_details 
WHERE faceScannedUrl IS NOT NULL 
AND faceScannedUrl != ''
AND id NOT IN (SELECT user_id FROM face_embeddings);
```

## Key Features Added

### 1. Face Embeddings Storage
- 512-dimensional ArcFace embeddings
- Confidence scores
- Quality metrics

### 2. Facial Landmarks
- 5-point facial landmarks
- Bounding boxes
- Age and gender estimation
- Face attributes

### 3. Recognition Logging
- All recognition attempts logged
- Similarity scores tracked
- Performance metrics
- Error tracking

### 4. Management Views
- `user_face_status` - Shows enrollment status for all users
- `recognition_stats` - Daily recognition statistics

## Important Notes

### Row Level Security (RLS)
- Tables have RLS enabled for security
- Service role has full access
- Anonymous users can read embeddings and log recognition attempts
- Adjust policies based on your security requirements

### Indexes
- All tables have proper indexes for performance
- Foreign key constraints available (commented out by default)

### Functions
- Automatic timestamp updates
- Cosine similarity calculation (JSONB version only)

## Next Steps

1. **Run the schema** - Choose and execute one of the provided SQL files
2. **Test the API** - Use the new endpoints to enroll and recognize faces
3. **Sync existing faces** - Use the `/sync-faces-from-db` endpoint to process existing face URLs
4. **Monitor performance** - Check the recognition_stats view for insights

## API Endpoints Added

- `POST /enroll` - Enroll a new face
- `POST /extract-landmarks` - Extract facial features
- `GET /faces` - List enrolled faces
- `DELETE /faces/{user_id}` - Remove a face
- `POST /sync-faces-from-db` - Process existing face URLs

## Troubleshooting

### If pgvector is not available:
1. Use the JSONB schema version
2. Contact Supabase support to enable pgvector extension
3. Or migrate to a PostgreSQL instance with pgvector support

### Performance Issues:
1. Check if indexes are created properly
2. Monitor query execution plans
3. Consider adding more specific indexes based on your query patterns

### RLS Issues:
1. Verify your authentication setup
2. Check policy definitions
3. Use service_role key for backend operations
