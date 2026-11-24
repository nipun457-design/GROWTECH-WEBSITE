"""
Secure Admin Account Setup Tool for GROWTECH ENGINEERS
Allows the owner to create or reset an authorized administrator account.
Supports both SQLite (local development) and PostgreSQL (production).
Never hardcodes passwords in source code.
"""
import sys
import os
import argparse
import getpass
from werkzeug.security import generate_password_hash
import db

def create_admin(username, password, email="growtechengineers911@gmail.com", full_name="Naresh Kumar"):
    if not username or len(username) < 3:
        print("Error: Username must be at least 3 characters.")
        return False
    if not password or len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        return False

    password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    conn = db.get_connection()

    # Check if username already exists
    cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing = cursor.fetchone()

    if existing:
        conn.execute('''
            UPDATE users SET password_hash = ?, email = ?, full_name = ? WHERE username = ?
        ''', (password_hash, email, full_name, username))
        print(f"Admin account '{username}' updated/reset successfully.")
    else:
        conn.execute('''
            INSERT INTO users (username, password_hash, email, full_name, role)
            VALUES (?, ?, ?, ?, 'admin')
        ''', (username, password_hash, email, full_name))
        print(f"Admin account '{username}' created successfully.")

    conn.commit()
    conn.close()
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create or update an admin account for GROWTECH ENGINEERS dashboard.")
    parser.add_argument('--username', help="Admin username")
    parser.add_argument('--password', help="Admin password")
    parser.add_argument('--email', default="growtechengineers911@gmail.com", help="Admin email")
    parser.add_argument('--fullname', default="Naresh Kumar", help="Admin full name")
    parser.add_argument('--reset-password', action='store_true', help="Flag indicating password reset")
    parser.add_argument('--interactive', action='store_true', help="Prompt interactively for credentials")

    args = parser.parse_args()

    # Check environment variables as fallback
    env_user = os.environ.get('ADMIN_USERNAME')
    env_pass = os.environ.get('ADMIN_PASSWORD')

    username = args.username or env_user
    password = args.password or env_pass

    if args.interactive or not username:
        username = input("Enter admin username: ").strip()
    if args.interactive or not password:
        password = getpass.getpass("Enter admin password (min 8 chars, hidden input): ").strip()

    create_admin(username, password, args.email, args.fullname)
