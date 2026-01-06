-- ============================================
-- Migration: Fix data_bank table and policies
-- Run this against your Supabase PostgreSQL
-- ============================================

-- Create data_bank table if it doesn't exist
CREATE TABLE IF NOT EXISTS data_bank (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    
    type TEXT NOT NULL CHECK (type IN ('statistic', 'quote', 'finding', 'aha_moment', 'recommendation')),
    content TEXT NOT NULL,
    context TEXT,
    source_page INTEGER,
    
    tags TEXT[] DEFAULT '{}',
    topic TEXT,
    
    speaker TEXT,
    value TEXT,
    unit TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_databank_report ON data_bank(report_id);
CREATE INDEX IF NOT EXISTS idx_databank_type ON data_bank(type);
CREATE INDEX IF NOT EXISTS idx_databank_tags ON data_bank USING gin(tags);

-- Enable RLS
ALTER TABLE data_bank ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to recreate them properly)
DROP POLICY IF EXISTS "Data bank is viewable by authenticated users" ON data_bank;
DROP POLICY IF EXISTS "Service role can manage data_bank" ON data_bank;

-- Allow authenticated users to read
CREATE POLICY "Data bank is viewable by authenticated users"
    ON data_bank FOR SELECT
    TO authenticated
    USING (true);

-- Allow service role full access (for backend processing)
-- Note: service_role bypasses RLS by default, but this is explicit
CREATE POLICY "Service role can manage data_bank"
    ON data_bank FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Grant permissions to service_role explicitly
GRANT ALL ON data_bank TO service_role;

-- Verify table exists
SELECT 'Migration 003 complete: data_bank table created/verified' AS status;
