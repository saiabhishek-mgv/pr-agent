# app.py - Contains intentional security vulnerabilities for testing

import os
import sqlite3

# Security Issue 1: Hardcoded secrets
API_KEY = "sk_live_1234567890abcdef"
DATABASE_PASSWORD = "admin123"
SECRET_TOKEN = "my_secret_token_12345"

# Security Issue 2: SQL Injection vulnerability
def get_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Vulnerable to SQL injection
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()

# Security Issue 3: Command injection
def run_command(filename):
    # Vulnerable to command injection
    os.system("cat " + filename)

# Security Issue 4: Using MD5 (weak crypto)
import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Performance Issue: N+1 query pattern
def get_all_user_posts():
    users = User.objects.all()
    for user in users:
        posts = Post.objects.filter(user=user)  # N+1 problem
        print(posts)

# Breaking change: Removing a public method
# def old_authenticate(username, password):
#     # This method was removed - breaking change!
#     pass

# New authentication method with different signature
def authenticate(email, password, remember_me=False):
    # Changed from username to email - breaking change
    pass
