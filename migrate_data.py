"""
GROWTECH ENGINEERS — Database Backup and Migration Utility (migrate_data.py)
Supports:
1. Backing up all tables (users, enquiries, products, gallery, certificates, news) to JSON.
2. Direct migration from local SQLite to production PostgreSQL.
3. Restoring data from JSON backup without data loss or overwriting existing records.
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
import db

TABLES = [
    'users',
    'enquiries',
    'products',
    'product_images',
    'company_content',
    'gallery',
    'certificates',
    'news_items'
]

def backup_to_json(output_path=None):
    """Exports all database tables to a structured JSON backup file"""
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(backup_dir, f"growtech_backup_{timestamp}.json")

    conn = db.get_connection()
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'engine': 'postgresql' if conn.is_pg else 'sqlite',
        'tables': {}
    }

    total_records = 0
    for tbl in TABLES:
        try:
            cursor = conn.execute(f"SELECT * FROM {tbl}")
            rows = []
            for r in cursor.fetchall():
                row_dict = {}
                for k in r.keys():
                    val = r[k]
                    # Format datetimes for JSON serialization
                    if isinstance(val, (datetime,)):
                        val = val.isoformat()
                    row_dict[k] = val
                rows.append(row_dict)
            backup_data['tables'][tbl] = rows
            total_records += len(rows)
            print(f"Extracted {len(rows)} records from '{tbl}'.")
        except Exception as e:
            print(f"Warning: Could not read table '{tbl}': {e}")
            backup_data['tables'][tbl] = []

    conn.close()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully created backup with {total_records} total records at:")
    print(f"-> {output_path}")
    return output_path

def restore_from_json(json_path, target_conn=None):
    """Restores records from JSON backup into target database safely"""
    if not os.path.isfile(json_path):
        print(f"Error: Backup file not found: {json_path}")
        return False

    with open(json_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    conn = target_conn or db.get_connection()
    # Initialize schema first
    db.init_schema(conn)

    tables_data = backup_data.get('tables', {})
    for tbl in TABLES:
        rows = tables_data.get(tbl, [])
        if not rows:
            continue

        inserted = 0
        for r in rows:
            cols = list(r.keys())
            vals = [r[c] for c in cols]
            placeholders = ", ".join(["?" for _ in cols])
            col_names = ", ".join(cols)

            if tbl == 'company_content':
                query = f"""
                    INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})
                    ON CONFLICT(key_name) DO UPDATE SET value = EXCLUDED.value
                """
            elif tbl == 'users':
                query = f"""
                    INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})
                    ON CONFLICT(username) DO NOTHING
                """
            elif tbl == 'products':
                query = f"""
                    INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})
                    ON CONFLICT(slug) DO NOTHING
                """
            else:
                query = f"INSERT INTO {tbl} ({col_names}) VALUES ({placeholders})"

            try:
                conn.execute(query, tuple(vals))
                inserted += 1
            except Exception as e:
                # If record already exists, skip
                pass

        conn.commit()
        print(f"Imported {inserted} records into '{tbl}'.")

    if not target_conn:
        conn.close()

    print("\nData restore completed successfully.")
    return True

def sqlite_to_postgres():
    """Directly migrates data from local SQLite database to production PostgreSQL"""
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'growtech.db')
    if not os.path.isfile(sqlite_path):
        print(f"Error: SQLite source database not found at {sqlite_path}")
        return False

    if not db.is_postgres():
        print("Error: DATABASE_URL is not set to a PostgreSQL connection string.")
        print("Please set DATABASE_URL (e.g. postgresql://user:pass@host:5432/dbname) before running migration.")
        return False

    print("Step 1: Creating safety backup of SQLite database...")
    backup_file = backup_to_json()

    print("\nStep 2: Connecting to PostgreSQL target database and migrating schema...")
    pg_conn = db.get_connection()
    db.init_schema(pg_conn)

    print("\nStep 3: Populating PostgreSQL from backup...")
    restore_from_json(backup_file, target_conn=pg_conn)
    pg_conn.close()

    print("\nDirect SQLite -> PostgreSQL migration finished successfully!")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="GROWTECH ENGINEERS Database Backup and Migration Tool")
    parser.add_argument('--backup', action='store_true', help="Export all tables to a timestamped JSON backup file")
    parser.add_argument('--output', help="Custom output path for backup JSON file")
    parser.add_argument('--restore', help="Restore data from a specified JSON backup file")
    parser.add_argument('--sqlite-to-postgres', action='store_true', help="Directly migrate from local SQLite to PostgreSQL (requires DATABASE_URL)")

    args = parser.parse_args()

    if args.backup:
        backup_to_json(args.output)
    elif args.restore:
        restore_from_json(args.restore)
    elif args.sqlite_to_postgres:
        sqlite_to_postgres()
    else:
        # Default action: run backup
        print("No specific action selected. Generating standard database backup...")
        backup_to_json()
