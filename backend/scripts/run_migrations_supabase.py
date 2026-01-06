#!/usr/bin/env python3
"""
Run database migrations via Supabase client (uses REST API).
This avoids direct PostgreSQL connection issues.

Usage:
    python scripts/run_migrations_supabase.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment
load_dotenv()

def run_migrations():
    """Run migrations via Supabase RPC."""
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        return False
    
    print(f"Connecting to Supabase: {supabase_url}")
    
    try:
        supabase = create_client(supabase_url, service_key)
        print("Connected to Supabase")
    except Exception as e:
        print(f"ERROR: Failed to connect: {e}")
        return False
    
    # Test connection by checking if reports table exists
    try:
        result = supabase.table("reports").select("id").limit(1).execute()
        print("Tables already exist! Migration may have been run already.")
        print("Checking existing data...")
        
        # Count existing records
        reports = supabase.table("reports").select("id", count="exact").execute()
        print(f"  - reports: {reports.count or 0} records")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "relation" in error_msg:
            print("Tables do not exist yet. Please run migration manually.")
            print()
            print("=" * 50)
            print("MANUAL MIGRATION REQUIRED")
            print("=" * 50)
            print()
            print("1. Open Supabase Dashboard")
            print("2. Go to SQL Editor")
            print("3. Create a new query")
            print("4. Copy contents from:")
            print(f"   {Path(__file__).parent.parent / 'migrations' / '001_initial_schema.sql'}")
            print("5. Click 'Run'")
            print()
            print("After running, execute this script again to verify.")
            return False
        else:
            print(f"Error checking tables: {e}")
            return False


if __name__ == "__main__":
    print("=" * 50)
    print("DCAI - Migration Check via Supabase Client")
    print("=" * 50)
    print()
    
    success = run_migrations()
    
    sys.exit(0 if success else 1)
