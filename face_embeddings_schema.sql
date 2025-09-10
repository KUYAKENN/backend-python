-- =============================================================================
-- FACE EMBEDDINGS DATABASE SCHEMA
-- Add these tables to your existing Supabase database
-- =============================================================================

-- 1. Create face_embeddings table to store ArcFace embeddings
CREATE TABLE IF NOT EXISTS face_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE, -- Links to your existing user_details.id
    embedding VECTOR(512) NOT NULL, -- 512-dimensional ArcFace embedding
    confidence REAL NOT NULL DEFAULT 0.0, -- Detection confidence score
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create face_landmarks table to store facial keypoints
CREATE TABLE IF NOT EXISTS face_landmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE, -- Links to your existing user_details.id
    landmarks JSONB NOT NULL, -- Array of 5 facial landmarks [x,y] coordinates
    bbox JSONB NOT NULL, -- Bounding box [x1, y1, x2, y2]
    age INTEGER, -- Estimated age
    gender TEXT, -- Estimated gender
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create face_recognition_log table for tracking recognition attempts
CREATE TABLE IF NOT EXISTS face_recognition_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recognized_user_id TEXT, -- NULL if no match found
    similarity_score REAL, -- Similarity score (0.0 to 1.0)
    recognition_status TEXT NOT NULL CHECK (recognition_status IN ('success', 'no_match', 'error')),
    error_message TEXT,
    image_metadata JSONB, -- Store image info like size, format, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_face_embeddings_user_id ON face_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_face_landmarks_user_id ON face_landmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_user_id ON face_recognition_log(recognized_user_id);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_created_at ON face_recognition_log(created_at);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_status ON face_recognition_log(recognition_status);

-- 5. Add foreign key constraints (if your user_details table uses UUID)
-- Uncomment and modify these if you want referential integrity
-- ALTER TABLE face_embeddings 
-- ADD CONSTRAINT fk_face_embeddings_user_id 
-- FOREIGN KEY (user_id) REFERENCES user_details(id) ON DELETE CASCADE;

-- ALTER TABLE face_landmarks 
-- ADD CONSTRAINT fk_face_landmarks_user_id 
-- FOREIGN KEY (user_id) REFERENCES user_details(id) ON DELETE CASCADE;

-- 6. Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. Create triggers for automatic timestamp updates
CREATE TRIGGER update_face_embeddings_updated_at 
BEFORE UPDATE ON face_embeddings 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_face_landmarks_updated_at 
BEFORE UPDATE ON face_landmarks 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. Enable Row Level Security (RLS) - Optional but recommended
ALTER TABLE face_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_landmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_recognition_log ENABLE ROW LEVEL SECURITY;

-- 9. Create policies for RLS (adjust according to your auth setup)
-- Service role can do everything
CREATE POLICY "Service role can manage face_embeddings" ON face_embeddings
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage face_landmarks" ON face_landmarks
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage face_recognition_log" ON face_recognition_log
FOR ALL USING (auth.role() = 'service_role');

-- Anonymous role can only read (for recognition)
CREATE POLICY "Anonymous can read face_embeddings" ON face_embeddings
FOR SELECT USING (true);

CREATE POLICY "Anonymous can insert recognition_log" ON face_recognition_log
FOR INSERT WITH CHECK (true);

-- =============================================================================
-- USEFUL QUERIES FOR FACE MANAGEMENT
-- =============================================================================

-- Query to check all users with face images in user_details
-- SELECT id, firstName, lastName, faceScannedUrl 
-- FROM user_details 
-- WHERE faceScannedUrl IS NOT NULL 
-- AND faceScannedUrl != '';

-- Query to check enrolled faces with user info
-- SELECT 
--     fe.user_id,
--     ud.firstName,
--     ud.lastName,
--     fe.confidence,
--     fe.created_at
-- FROM face_embeddings fe
-- JOIN user_details ud ON fe.user_id = ud.id;

-- Query to get face recognition statistics
-- SELECT 
--     recognition_status,
--     COUNT(*) as count,
--     AVG(similarity_score) as avg_similarity
-- FROM face_recognition_log 
-- GROUP BY recognition_status;

-- Query to find users without face embeddings
-- SELECT ud.id, ud.firstName, ud.lastName, ud.faceScannedUrl
-- FROM user_details ud
-- LEFT JOIN face_embeddings fe ON ud.id = fe.user_id
-- WHERE fe.user_id IS NULL
-- AND ud.faceScannedUrl IS NOT NULL 
-- AND ud.faceScannedUrl != '';

-- =============================================================================
-- NOTES:
-- =============================================================================
-- 1. The VECTOR(512) type requires the pgvector extension in PostgreSQL
-- 2. If pgvector is not available, you can use JSONB to store embeddings as arrays
-- 3. Adjust the foreign key constraints based on your actual user table structure
-- 4. The RLS policies assume you're using Supabase auth - modify as needed
-- 5. Consider adding additional indexes based on your query patterns
-- =============================================================================
