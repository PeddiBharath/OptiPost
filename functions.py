import re
from supabase import create_client
import streamlit as st

# Initialize Supabase client and resend
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# Email validation function
def is_valid_email(email):
    email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(email_regex, email)

def new_verified(email,role):
    check = supabase.table("users").select("*").eq("email", email).execute()
    if not check.data :
        supabase.table("users").insert({"email": email, "role":role}).execute()

def check_role(email, role):
    result = (
        supabase.table("users").select("email").eq("email", email).eq("role", role).execute()
    )
    if result.data:
        return True
    else:
        return False