#!/usr/bin/env python3
"""
Validate that all required environment variables are set.

Usage:
    python scripts/validate_env.py
"""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Required variables
REQUIRED = [
    ("OPENROUTER_API_KEY", "LLM access via OpenRouter"),
    ("SUPABASE_URL", "Supabase instance URL"),
    ("SUPABASE_ANON_KEY", "Supabase anonymous key"),
    ("SUPABASE_SERVICE_KEY", "Supabase service role key"),
    ("DATABASE_URL", "PostgreSQL connection string"),
]

# Optional but recommended
RECOMMENDED = [
    ("RAGFLOW_API_KEY", "RAGFlow API key (get after first login)"),
    ("FIRECRAWL_API_KEY", "Firecrawl for news scraping"),
    ("TAVILY_API_KEY", "Tavily for web search"),
    ("JWT_SECRET", "JWT signing secret"),
]

def validate():
    """Check environment variables."""
    print("=" * 50)
    print("DCAI Intelligence Platform - Environment Validation")
    print("=" * 50)
    print()
    
    missing_required = []
    missing_recommended = []
    
    # Check required
    print("Required Variables:")
    for var, desc in REQUIRED:
        value = os.getenv(var, "")
        if value and value != "[FILL]" and not value.startswith("["):
            # Mask the value
            masked = value[:4] + "..." + value[-4:] if len(value) > 10 else "****"
            print(f"  [OK] {var}: {masked}")
        else:
            print(f"  [MISSING] {var}: {desc}")
            missing_required.append(var)
    
    print()
    print("Recommended Variables:")
    for var, desc in RECOMMENDED:
        value = os.getenv(var, "")
        if value and value != "[FILL]" and not value.startswith("["):
            masked = value[:4] + "..." + value[-4:] if len(value) > 10 else "****"
            print(f"  [OK] {var}: {masked}")
        else:
            print(f"  [MISSING] {var}: {desc}")
            missing_recommended.append(var)
    
    print()
    print("=" * 50)
    
    if missing_required:
        print(f"ERROR: {len(missing_required)} required variable(s) missing!")
        print(f"Missing: {', '.join(missing_required)}")
        print()
        print("Please edit .env and fill in the missing values.")
        return False
    
    if missing_recommended:
        print(f"WARNING: {len(missing_recommended)} recommended variable(s) missing.")
        print("Some features may not work without these.")
    
    print("Environment validation PASSED")
    return True


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
