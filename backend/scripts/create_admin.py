#!/usr/bin/env python3
"""
Create the initial admin user in Supabase.

Usage:
    python scripts/create_admin.py
"""
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
load_dotenv()


def create_admin_user():
    """Create the admin user in Supabase."""
    
    # Get config from environment
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    admin_email = os.getenv("ADMIN_EMAIL", "s.falasi@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        sys.exit(1)
    
    if not admin_password:
        print("ERROR: ADMIN_PASSWORD must be set")
        sys.exit(1)
    
    print(f"Creating admin user: {admin_email}")
    
    # Create Supabase client with service key (admin access)
    supabase: Client = create_client(supabase_url, service_key)
    
    try:
        # Check if user already exists
        # Note: This requires the service role key
        existing = supabase.auth.admin.list_users()
        
        for user in existing:
            if user.email == admin_email:
                print(f"User {admin_email} already exists (ID: {user.id})")
                
                # Update to ensure is_admin flag is set
                supabase.auth.admin.update_user_by_id(
                    user.id,
                    {"user_metadata": {"is_admin": True}}
                )
                print("Updated user metadata with is_admin=True")
                return
        
        # Create new user
        response = supabase.auth.admin.create_user({
            "email": admin_email,
            "password": admin_password,
            "email_confirm": True,  # Skip email confirmation
            "user_metadata": {
                "is_admin": True,
                "full_name": "Salem Al Falasi"
            }
        })
        
        print(f"Created admin user successfully!")
        print(f"  Email: {admin_email}")
        print(f"  User ID: {response.user.id}")
        print(f"  Is Admin: True")
        
    except Exception as e:
        print(f"ERROR: Failed to create user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin_user()
