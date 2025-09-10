-- =============================================================================
-- ALTERNATIVE FACE EMBEDDINGS SCHEMA (WITHOUT PGVECTOR EXTENSION)
-- Use this if your Supabase instance doesn't have pgvector enabled
-- =============================================================================

-- 1. Create face_embeddings table using JSONB for embeddings
CREATE TABLE IF NOT EXISTS face_embeddings (
    id TEXT NOT NULL DEFAULT ('face_emb_' || substr(gen_random_uuid()::text, 1, 12)) PRIMARY KEY,
    user_detail_id TEXT NOT NULL UNIQUE, -- Links to your existing user_details.id
    user_id TEXT NOT NULL, -- Links to users.id for consistency
    embedding JSONB NOT NULL, -- 512-dimensional ArcFace embedding as JSON array
    embedding_size INTEGER NOT NULL DEFAULT 512, -- Dimension of the embedding
    confidence REAL NOT NULL DEFAULT 0.0, -- Detection confidence score
    face_quality_score REAL DEFAULT 0.0, -- Additional quality metric
    source_url TEXT, -- Original faceScannedUrl from user_details
    enrollment_method TEXT DEFAULT 'api', -- 'api', 'sync', 'manual'
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT valid_quality CHECK (face_quality_score >= 0.0 AND face_quality_score <= 1.0),
    CONSTRAINT fk_face_embeddings_user_detail FOREIGN KEY (user_detail_id) REFERENCES user_details(id) ON DELETE CASCADE,
    CONSTRAINT fk_face_embeddings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. Create face_landmarks table
CREATE TABLE IF NOT EXISTS face_landmarks (
    id TEXT NOT NULL DEFAULT ('face_lm_' || substr(gen_random_uuid()::text, 1, 12)) PRIMARY KEY,
    user_detail_id TEXT NOT NULL UNIQUE, -- Links to your existing user_details.id
    user_id TEXT NOT NULL, -- Links to users.id for consistency
    landmarks JSONB NOT NULL, -- Array of 5 facial landmarks [[x1,y1], [x2,y2], ...]
    bbox JSONB NOT NULL, -- Bounding box [x1, y1, x2, y2]
    face_area REAL, -- Calculated face area in pixels
    face_angle REAL, -- Face rotation angle
    age INTEGER, -- Estimated age
    gender TEXT CHECK (gender IN ('male', 'female')), -- Estimated gender
    emotion JSONB, -- Emotion scores if available
    face_attributes JSONB, -- Additional attributes (glasses, beard, etc.)
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_age CHECK (age IS NULL OR (age >= 0 AND age <= 120)),
    CONSTRAINT valid_face_area CHECK (face_area IS NULL OR face_area > 0),
    CONSTRAINT fk_face_landmarks_user_detail FOREIGN KEY (user_detail_id) REFERENCES user_details(id) ON DELETE CASCADE,
    CONSTRAINT fk_face_landmarks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Create face_recognition_log table
CREATE TABLE IF NOT EXISTS face_recognition_log (
    id TEXT NOT NULL DEFAULT ('face_rec_' || substr(gen_random_uuid()::text, 1, 12)) PRIMARY KEY,
    session_id TEXT, -- Optional session tracking
    recognized_user_detail_id TEXT, -- NULL if no match found - links to user_details.id
    recognized_user_id TEXT, -- Links to users.id
    similarity_score REAL, -- Best similarity score (0.0 to 1.0)
    threshold_used REAL NOT NULL, -- Recognition threshold used
    candidates_count INTEGER DEFAULT 0, -- Number of candidates checked
    recognition_status TEXT NOT NULL CHECK (recognition_status IN ('success', 'no_match', 'multiple_matches', 'error', 'low_quality')),
    error_message TEXT,
    processing_time_ms INTEGER, -- Processing time in milliseconds
    image_metadata JSONB, -- Store image info like size, format, quality
    all_similarities JSONB, -- Store all similarity scores for debugging
    attendance_marked BOOLEAN DEFAULT FALSE, -- Whether attendance was marked
    attendance_id TEXT, -- Link to attendance record if created
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET, -- Track recognition attempts by IP
    user_agent TEXT, -- Track client info
    
    -- Constraints
    CONSTRAINT valid_similarity CHECK (similarity_score IS NULL OR (similarity_score >= 0.0 AND similarity_score <= 1.0)),
    CONSTRAINT valid_threshold CHECK (threshold_used >= 0.0 AND threshold_used <= 1.0),
    CONSTRAINT valid_processing_time CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0),
    CONSTRAINT fk_face_recognition_user_detail FOREIGN KEY (recognized_user_detail_id) REFERENCES user_details(id),
    CONSTRAINT fk_face_recognition_user FOREIGN KEY (recognized_user_id) REFERENCES users(id),
    CONSTRAINT fk_face_recognition_attendance FOREIGN KEY (attendance_id) REFERENCES attendance(id)
);

-- 4. Create face_enrollment_log table to track enrollment attempts
CREATE TABLE IF NOT EXISTS face_enrollment_log (
    id TEXT NOT NULL DEFAULT ('face_enr_' || substr(gen_random_uuid()::text, 1, 12)) PRIMARY KEY,
    user_detail_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    enrollment_status TEXT NOT NULL CHECK (enrollment_status IN ('success', 'failed', 'updated')),
    face_count_detected INTEGER DEFAULT 0,
    face_quality_score REAL,
    error_message TEXT,
    image_source TEXT, -- 'upload', 'url', 'webcam', 'sync_from_db', etc.
    source_url TEXT, -- Original URL if from database sync
    image_metadata JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_face_count CHECK (face_count_detected >= 0),
    CONSTRAINT fk_face_enrollment_user_detail FOREIGN KEY (user_detail_id) REFERENCES user_details(id) ON DELETE CASCADE,
    CONSTRAINT fk_face_enrollment_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Create comprehensive indexes
CREATE INDEX IF NOT EXISTS idx_face_embeddings_user_detail_id ON face_embeddings(user_detail_id);
CREATE INDEX IF NOT EXISTS idx_face_embeddings_user_id ON face_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_face_embeddings_created_at ON face_embeddings(created_at);
CREATE INDEX IF NOT EXISTS idx_face_embeddings_confidence ON face_embeddings(confidence);

CREATE INDEX IF NOT EXISTS idx_face_landmarks_user_detail_id ON face_landmarks(user_detail_id);
CREATE INDEX IF NOT EXISTS idx_face_landmarks_user_id ON face_landmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_face_landmarks_age ON face_landmarks(age);
CREATE INDEX IF NOT EXISTS idx_face_landmarks_gender ON face_landmarks(gender);

CREATE INDEX IF NOT EXISTS idx_face_recognition_log_user_detail_id ON face_recognition_log(recognized_user_detail_id);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_user_id ON face_recognition_log(recognized_user_id);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_created_at ON face_recognition_log(created_at);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_status ON face_recognition_log(recognition_status);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_similarity ON face_recognition_log(similarity_score);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_session ON face_recognition_log(session_id);
CREATE INDEX IF NOT EXISTS idx_face_recognition_log_attendance ON face_recognition_log(attendance_id);

CREATE INDEX IF NOT EXISTS idx_face_enrollment_log_user_detail_id ON face_enrollment_log(user_detail_id);
CREATE INDEX IF NOT EXISTS idx_face_enrollment_log_user_id ON face_enrollment_log(user_id);
CREATE INDEX IF NOT EXISTS idx_face_enrollment_log_status ON face_enrollment_log(enrollment_status);
CREATE INDEX IF NOT EXISTS idx_face_enrollment_log_created_at ON face_enrollment_log(created_at);

-- 6. Create or replace functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to calculate cosine similarity between two embeddings stored as JSONB
CREATE OR REPLACE FUNCTION cosine_similarity(embedding1 JSONB, embedding2 JSONB)
RETURNS REAL AS $$
DECLARE
    dot_product REAL := 0;
    norm1 REAL := 0;
    norm2 REAL := 0;
    i INTEGER;
    val1 REAL;
    val2 REAL;
    size1 INTEGER;
    size2 INTEGER;
BEGIN
    -- Get array sizes
    size1 := jsonb_array_length(embedding1);
    size2 := jsonb_array_length(embedding2);
    
    -- Check if embeddings have same size
    IF size1 != size2 THEN
        RETURN 0;
    END IF;
    
    -- Calculate dot product and norms
    FOR i IN 0..(size1-1) LOOP
        val1 := (embedding1->i)::REAL;
        val2 := (embedding2->i)::REAL;
        
        dot_product := dot_product + (val1 * val2);
        norm1 := norm1 + (val1 * val1);
        norm2 := norm2 + (val2 * val2);
    END LOOP;
    
    -- Avoid division by zero
    IF norm1 = 0 OR norm2 = 0 THEN
        RETURN 0;
    END IF;
    
    -- Return cosine similarity
    RETURN dot_product / (sqrt(norm1) * sqrt(norm2));
END;
$$ language 'plpgsql';

-- 7. Create triggers
CREATE TRIGGER update_face_embeddings_updated_at 
BEFORE UPDATE ON face_embeddings 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_face_landmarks_updated_at 
BEFORE UPDATE ON face_landmarks 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. Enable Row Level Security
ALTER TABLE face_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_landmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_recognition_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_enrollment_log ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS Policies
CREATE POLICY "Service role full access face_embeddings" ON face_embeddings
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access face_landmarks" ON face_landmarks
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access face_recognition_log" ON face_recognition_log
FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access face_enrollment_log" ON face_enrollment_log
FOR ALL USING (auth.role() = 'service_role');

-- Allow anonymous/authenticated users to read embeddings for recognition
CREATE POLICY "Public read face_embeddings" ON face_embeddings
FOR SELECT USING (true);

-- Allow logging recognition attempts
CREATE POLICY "Public insert recognition_log" ON face_recognition_log
FOR INSERT WITH CHECK (true);

-- =============================================================================
-- USEFUL QUERIES AND VIEWS
-- =============================================================================

-- View combining user details with face enrollment status
CREATE OR REPLACE VIEW user_face_status AS
SELECT 
    ud.id as user_detail_id,
    ud."userId" as user_id,
    ud."firstName",
    ud."lastName",
    ud."middleName",
    ud."faceScannedUrl",
    ua.email,
    ua."mobileNumber",
    ua.user_type,
    CASE 
        WHEN fe.user_detail_id IS NOT NULL THEN 'enrolled'
        WHEN ud."faceScannedUrl" IS NOT NULL AND ud."faceScannedUrl" != '' THEN 'pending'
        ELSE 'no_image'
    END as enrollment_status,
    fe.confidence,
    fe.created_at as enrolled_at,
    fl.age,
    fl.gender,
    fe.enrollment_method,
    fe.source_url
FROM user_details ud
LEFT JOIN user_accounts ua ON ud."userId" = ua."userId"
LEFT JOIN face_embeddings fe ON ud.id = fe.user_detail_id
LEFT JOIN face_landmarks fl ON ud.id = fl.user_detail_id;

-- View for recognition statistics
CREATE OR REPLACE VIEW recognition_stats AS
SELECT 
    DATE(created_at) as date,
    recognition_status,
    COUNT(*) as attempts,
    AVG(similarity_score) as avg_similarity,
    MIN(similarity_score) as min_similarity,
    MAX(similarity_score) as max_similarity,
    AVG(processing_time_ms) as avg_processing_time
FROM face_recognition_log
GROUP BY DATE(created_at), recognition_status
ORDER BY date DESC, recognition_status;

-- =============================================================================
-- SPECIFIC QUERIES FOR YOUR DATABASE STRUCTURE
-- =============================================================================

-- 1. Find all users with face images ready for enrollment
SELECT 
    ud.id as user_detail_id,
    ud."userId" as user_id,
    ud."firstName",
    ud."lastName",
    ud."faceScannedUrl",
    ua.email,
    ua.user_type
FROM user_details ud
JOIN user_accounts ua ON ud."userId" = ua."userId"
WHERE ud."faceScannedUrl" IS NOT NULL 
AND ud."faceScannedUrl" != ''
AND NOT EXISTS (
    SELECT 1 FROM face_embeddings fe WHERE fe.user_detail_id = ud.id
);

-- 2. Get enrollment statistics by user type
SELECT 
    ua.user_type,
    COUNT(ud.id) as total_users,
    COUNT(ud."faceScannedUrl") as users_with_face_images,
    COUNT(fe.user_detail_id) as enrolled_users,
    ROUND(
        COUNT(fe.user_detail_id)::NUMERIC / 
        NULLIF(COUNT(ud."faceScannedUrl"), 0) * 100, 2
    ) as enrollment_percentage
FROM user_details ud
JOIN user_accounts ua ON ud."userId" = ua."userId"
LEFT JOIN face_embeddings fe ON ud.id = fe.user_detail_id
GROUP BY ua.user_type
ORDER BY total_users DESC;

-- 3. Recognition success rate by day
SELECT 
    DATE(created_at) as recognition_date,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN recognition_status = 'success' THEN 1 END) as successful_recognitions,
    ROUND(
        COUNT(CASE WHEN recognition_status = 'success' THEN 1 END)::NUMERIC / 
        COUNT(*) * 100, 2
    ) as success_rate_percent,
    AVG(similarity_score) as avg_similarity,
    AVG(processing_time_ms) as avg_processing_time
FROM face_recognition_log
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY recognition_date DESC;

-- 4. Most recognized users (attendance tracking)
SELECT 
    frl.recognized_user_detail_id,
    ud."firstName",
    ud."lastName",
    ua.email,
    ua.user_type,
    COUNT(*) as recognition_count,
    COUNT(CASE WHEN frl.attendance_marked = TRUE THEN 1 END) as attendance_marked_count,
    MAX(frl.created_at) as last_recognition,
    AVG(frl.similarity_score) as avg_similarity
FROM face_recognition_log frl
JOIN user_details ud ON frl.recognized_user_detail_id = ud.id
JOIN user_accounts ua ON ud."userId" = ua."userId"
WHERE frl.recognition_status = 'success'
AND frl.created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY frl.recognized_user_detail_id, ud."firstName", ud."lastName", ua.email, ua.user_type
ORDER BY recognition_count DESC
LIMIT 20;

-- 5. Face quality distribution
SELECT 
    CASE 
        WHEN fe.confidence >= 0.9 THEN 'Excellent (≥0.9)'
        WHEN fe.confidence >= 0.8 THEN 'Good (0.8-0.89)'
        WHEN fe.confidence >= 0.7 THEN 'Fair (0.7-0.79)'
        WHEN fe.confidence >= 0.6 THEN 'Poor (0.6-0.69)'
        ELSE 'Very Poor (<0.6)'
    END as quality_category,
    COUNT(*) as count,
    ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM face_embeddings) * 100, 2) as percentage
FROM face_embeddings fe
GROUP BY 
    CASE 
        WHEN fe.confidence >= 0.9 THEN 'Excellent (≥0.9)'
        WHEN fe.confidence >= 0.8 THEN 'Good (0.8-0.89)'
        WHEN fe.confidence >= 0.7 THEN 'Fair (0.7-0.79)'
        WHEN fe.confidence >= 0.6 THEN 'Poor (0.6-0.69)'
        ELSE 'Very Poor (<0.6)'
    END
ORDER BY 
    CASE 
        WHEN fe.confidence >= 0.9 THEN 1
        WHEN fe.confidence >= 0.8 THEN 2
        WHEN fe.confidence >= 0.7 THEN 3
        WHEN fe.confidence >= 0.6 THEN 4
        ELSE 5
    END;

-- 6. Users without face enrollment but with attendance records
SELECT 
    a."userId",
    ud."firstName",
    ud."lastName",
    ua.email,
    ua.user_type,
    COUNT(a.id) as attendance_count,
    MAX(a."scanTime") as last_attendance,
    ud."faceScannedUrl" IS NOT NULL as has_face_image
FROM attendance a
JOIN user_details ud ON a."userId" = ud."userId"
JOIN user_accounts ua ON a."userId" = ua."userId"
LEFT JOIN face_embeddings fe ON ud.id = fe.user_detail_id
WHERE fe.user_detail_id IS NULL
AND a."scanTime" >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a."userId", ud."firstName", ud."lastName", ua.email, ua.user_type, ud."faceScannedUrl"
ORDER BY attendance_count DESC;

-- 7. Sync candidates - Users ready for face enrollment
SELECT 
    'Ready for sync' as status,
    COUNT(*) as count
FROM user_details ud
WHERE ud."faceScannedUrl" IS NOT NULL 
AND ud."faceScannedUrl" != ''
AND NOT EXISTS (SELECT 1 FROM face_embeddings fe WHERE fe.user_detail_id = ud.id)

UNION ALL

SELECT 
    'Already enrolled' as status,
    COUNT(*) as count
FROM face_embeddings

UNION ALL

SELECT 
    'No face image' as status,
    COUNT(*) as count
FROM user_details ud
WHERE ud."faceScannedUrl" IS NULL OR ud."faceScannedUrl" = '';

-- 8. Recent enrollment activity
SELECT 
    fel.created_at,
    fel.enrollment_status,
    ud."firstName",
    ud."lastName",
    ua.email,
    ua.user_type,
    fel.image_source,
    fel.face_quality_score,
    fel.processing_time_ms,
    fel.error_message
FROM face_enrollment_log fel
JOIN user_details ud ON fel.user_detail_id = ud.id
JOIN user_accounts ua ON ud."userId" = ua."userId"
ORDER BY fel.created_at DESC
LIMIT 50;
