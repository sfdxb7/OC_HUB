-- ============================================
-- Migration: Add missing columns to reports table
-- Run this against your Supabase PostgreSQL
-- ============================================

-- Add missing columns to reports table if they don't exist
DO $$
BEGIN
    -- executive_summary
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'executive_summary') THEN
        ALTER TABLE reports ADD COLUMN executive_summary TEXT;
    END IF;

    -- key_findings
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'key_findings') THEN
        ALTER TABLE reports ADD COLUMN key_findings JSONB DEFAULT '[]';
    END IF;

    -- statistics
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'statistics') THEN
        ALTER TABLE reports ADD COLUMN statistics JSONB DEFAULT '[]';
    END IF;

    -- quotes
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'quotes') THEN
        ALTER TABLE reports ADD COLUMN quotes JSONB DEFAULT '[]';
    END IF;

    -- aha_moments
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'aha_moments') THEN
        ALTER TABLE reports ADD COLUMN aha_moments JSONB DEFAULT '[]';
    END IF;

    -- recommendations
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'recommendations') THEN
        ALTER TABLE reports ADD COLUMN recommendations JSONB DEFAULT '[]';
    END IF;

    -- methodology
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'methodology') THEN
        ALTER TABLE reports ADD COLUMN methodology TEXT;
    END IF;

    -- limitations
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'limitations') THEN
        ALTER TABLE reports ADD COLUMN limitations TEXT;
    END IF;

    -- mineru_folder
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'mineru_folder') THEN
        ALTER TABLE reports ADD COLUMN mineru_folder TEXT;
    END IF;

    -- ragflow_doc_id
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'ragflow_doc_id') THEN
        ALTER TABLE reports ADD COLUMN ragflow_doc_id TEXT;
    END IF;

    -- processing_status
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'processing_status') THEN
        ALTER TABLE reports ADD COLUMN processing_status TEXT DEFAULT 'pending';
    END IF;

    -- processed_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'reports' AND column_name = 'processed_at') THEN
        ALTER TABLE reports ADD COLUMN processed_at TIMESTAMPTZ;
    END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_reports_source ON reports(source);
CREATE INDEX IF NOT EXISTS idx_reports_year ON reports(year);
CREATE INDEX IF NOT EXISTS idx_reports_ragflow ON reports(ragflow_doc_id);

-- Output confirmation
SELECT 'Migration 002 complete: Added missing columns to reports table' AS status;
