-- =============================================================================
-- PERMISSION FIX FOR SERVICE_ROLE
-- Run this in your Supabase SQL Editor to fix permission issues
-- =============================================================================

-- 1. Grant schema permissions to service_role
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- 2. Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;

-- 3. Disable RLS for service_role on critical tables (if they exist)
DO $$ 
BEGIN
    -- Disable RLS for user_details if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_details') THEN
        EXECUTE 'ALTER TABLE user_details DISABLE ROW LEVEL SECURITY';
    END IF;
    
    -- Disable RLS for user_accounts if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_accounts') THEN
        EXECUTE 'ALTER TABLE user_accounts DISABLE ROW LEVEL SECURITY';
    END IF;
    
    -- Disable RLS for attendance if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'attendance') THEN
        EXECUTE 'ALTER TABLE attendance DISABLE ROW LEVEL SECURITY';
    END IF;
    
    -- Disable RLS for face_embeddings if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'face_embeddings') THEN
        EXECUTE 'ALTER TABLE face_embeddings DISABLE ROW LEVEL SECURITY';
    END IF;
    
    -- Disable RLS for face_landmarks if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'face_landmarks') THEN
        EXECUTE 'ALTER TABLE face_landmarks DISABLE ROW LEVEL SECURITY';
    END IF;
    
    -- Disable RLS for face_recognition_log if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'face_recognition_log') THEN
        EXECUTE 'ALTER TABLE face_recognition_log DISABLE ROW LEVEL SECURITY';
    END IF;
    
    -- Disable RLS for face_enrollment_log if it exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'face_enrollment_log') THEN
        EXECUTE 'ALTER TABLE face_enrollment_log DISABLE ROW LEVEL SECURITY';
    END IF;
END $$;

-- 4. Create attendance table if it doesn't exist
CREATE TABLE IF NOT EXISTS attendance (
    id TEXT NOT NULL DEFAULT ('att_' || substr(gen_random_uuid()::text, 1, 12)) PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "scanDate" DATE NOT NULL DEFAULT CURRENT_DATE,
    "scanTime" TIME NOT NULL DEFAULT CURRENT_TIME,
    "timeIn" TIMESTAMP,
    "timeOut" TIMESTAMP,
    status TEXT DEFAULT 'present' CHECK (status IN ('present', 'late', 'absent')),
    method TEXT DEFAULT 'face_recognition',
    confidence REAL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create indexes for attendance
CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance("userId", "scanDate");
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance("scanDate");

-- 6. Grant specific permissions on attendance table
GRANT ALL ON attendance TO service_role;
ALTER TABLE attendance DISABLE ROW LEVEL SECURITY;

-- 7. Verification query - check what tables exist
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- 8. Check service_role permissions
SELECT 
    grantee,
    table_name,
    privilege_type
FROM information_schema.role_table_grants 
WHERE grantee = 'service_role' 
AND table_schema = 'public'
ORDER BY table_name;

-- =============================================================================
-- INSTRUCTIONS:
-- 1. Copy this entire SQL block
-- 2. Go to Supabase Dashboard > SQL Editor
-- 3. Paste and run this SQL
-- 4. Restart your Flask application
-- =============================================================================