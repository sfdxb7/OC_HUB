"""
Create the data_bank table in Supabase.
Run this once before reprocessing to fix the missing table issue.
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
import requests

# Load environment
base_path = Path(__file__).parent.parent
load_dotenv(base_path / ".env.local", override=True)
load_dotenv(base_path / ".env", override=False)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    sys.exit(1)

# SQL to create data_bank table
CREATE_TABLE_SQL = """
-- Create data_bank table if not exists
CREATE TABLE IF NOT EXISTS public.data_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES public.reports(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    source_page INTEGER,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_data_bank_report_id ON public.data_bank(report_id);
CREATE INDEX IF NOT EXISTS idx_data_bank_type ON public.data_bank(type);

-- Enable RLS
ALTER TABLE public.data_bank ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS data_bank_select_policy ON public.data_bank;
DROP POLICY IF EXISTS data_bank_all_policy ON public.data_bank;

-- Allow authenticated users to read
CREATE POLICY data_bank_select_policy ON public.data_bank 
    FOR SELECT TO authenticated USING (true);

-- Allow service role full access  
CREATE POLICY data_bank_all_policy ON public.data_bank 
    FOR ALL TO service_role USING (true);
"""

def main():
    print("Creating data_bank table in Supabase...")
    print(f"URL: {SUPABASE_URL}")
    
    # Use the postgres REST endpoint with raw SQL
    # This requires the pg_graphql or similar extension, or we use supabase-py
    
    try:
        from supabase import create_client
        
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Execute raw SQL via rpc if available, otherwise we need dashboard
        # Try using postgrest's /rpc endpoint
        result = client.rpc('exec_sql', {'sql': CREATE_TABLE_SQL}).execute()
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Direct SQL execution not available: {e}")
        print("\n" + "="*60)
        print("MANUAL STEP REQUIRED")
        print("="*60)
        print("\nPlease run this SQL in the Supabase Dashboard SQL Editor:")
        print("1. Go to: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Paste and run this SQL:\n")
        print("-" * 40)
        print(CREATE_TABLE_SQL)
        print("-" * 40)
        
        # Also save to file for easy copy
        sql_file = Path(__file__).parent / "create_databank.sql"
        sql_file.write_text(CREATE_TABLE_SQL)
        print(f"\nSQL also saved to: {sql_file}")


if __name__ == "__main__":
    main()
