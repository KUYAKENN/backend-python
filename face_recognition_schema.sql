-- SQL Schema for Face Recognition System
-- This creates tables to store face embeddings and landmarks in your Supabase database

-- Create face_embeddings table to store facial recognition data
CREATE TABLE IF NOT EXISTS face_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_detail_id UUID REFERENCES user_details(id) ON DELETE SET NULL,
    
    -- Face embedding data (512-dimensional vector for ArcFace)
    embedding VECTOR(512), -- Use pgvector extension for efficient similarity search
    
    -- Face metadata
    bbox_x1 FLOAT,
    bbox_y1 FLOAT, 
    bbox_x2 FLOAT,
    bbox_y2 FLOAT,
    confidence FLOAT NOT NULL,
    
    -- Facial landmarks (5 key points: left eye, right eye, nose, left mouth corner, right mouth corner)
    landmarks JSONB, -- Store as JSON array of [x,y] coordinates
    
    -- Additional face attributes
    estimated_age INTEGER,
    estimated_gender TEXT,
    
    -- Source information
    source_image_url TEXT,
    enrollment_method TEXT DEFAULT 'api', -- 'api', 'batch_import', 'manual'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for faster queries
    CONSTRAINT unique_user_embedding UNIQUE(user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_face_embeddings_user_id ON face_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_face_embeddings_confidence ON face_embeddings(confidence);
CREATE INDEX IF NOT EXISTS idx_face_embeddings_created_at ON face_embeddings(created_at);

-- If using pgvector extension for similarity search:
-- CREATE INDEX IF NOT EXISTS idx_face_embeddings_vector ON face_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_face_embeddings_updated_at 
    BEFORE UPDATE ON face_embeddings 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Create face_recognition_logs table to track recognition events
CREATE TABLE IF NOT EXISTS face_recognition_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    recognition_confidence FLOAT NOT NULL,
    recognition_method TEXT DEFAULT 'camera', -- 'camera', 'upload', 'test'
    
    -- Recognition result details
    bbox_x1 FLOAT,
    bbox_y1 FLOAT,
    bbox_x2 FLOAT, 
    bbox_y2 FLOAT,
    landmarks JSONB,
    
    -- Attendance link (if this recognition resulted in attendance)
    attendance_id UUID REFERENCES attendance(id) ON DELETE SET NULL,
    
    -- Timestamp
    recognized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional metadata
    device_info JSONB,
    session_id TEXT
);

-- Index for recognition logs
CREATE INDEX IF NOT EXISTS idx_face_recognition_logs_user_id ON face_recognition_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_face_recognition_logs_recognized_at ON face_recognition_logs(recognized_at);

-- Create a view for easier querying of user face data
CREATE OR REPLACE VIEW user_face_data AS
SELECT 
    u.id as user_id,
    ud.firstName,
    ud.lastName,
    ud.middleName,
    ud.faceScannedUrl,
    fe.embedding,
    fe.bbox_x1,
    fe.bbox_y1,
    fe.bbox_x2,
    fe.bbox_y2,
    fe.confidence,
    fe.landmarks,
    fe.estimated_age,
    fe.estimated_gender,
    fe.source_image_url,
    fe.created_at as embedding_created_at,
    fe.updated_at as embedding_updated_at
FROM users u
LEFT JOIN user_details ud ON u.id = ud.userId
LEFT JOIN face_embeddings fe ON u.id = fe.user_id;

-- Grant permissions (adjust based on your RLS policies)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON face_embeddings TO authenticated;
-- GRANT SELECT, INSERT ON face_recognition_logs TO authenticated;
-- GRANT SELECT ON user_face_data TO authenticated;

-- Example queries for using the new tables:

-- 1. Find users who don't have face embeddings yet
-- SELECT u.id, ud.firstName, ud.lastName, ud.faceScannedUrl 
-- FROM users u
-- LEFT JOIN user_details ud ON u.id = ud.userId
-- LEFT JOIN face_embeddings fe ON u.id = fe.user_id
-- WHERE fe.id IS NULL AND ud.faceScannedUrl IS NOT NULL;

-- 2. Get all face recognition data for a user
-- SELECT * FROM user_face_data WHERE user_id = 'your-user-id';

-- 3. Find most recent recognitions
-- SELECT u.firstName, u.lastName, frl.recognition_confidence, frl.recognized_at
-- FROM face_recognition_logs frl
-- JOIN users u ON frl.user_id = u.id
-- ORDER BY frl.recognized_at DESC
-- LIMIT 10;
