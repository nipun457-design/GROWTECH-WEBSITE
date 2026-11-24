"""
GROWTECH ENGINEERS — Database Abstraction Module (db.py)
Provides unified interface for both SQLite (local development) and PostgreSQL (production).
Automatically detects DATABASE_URL and translates queries, parameters, and row formats.
"""

import os
import re
import json
import sqlite3
import urllib.parse
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL', '')
DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'growtech.db')

def is_postgres():
    return bool(DATABASE_URL and (DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')))

def get_db_url():
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url

class RowWrapper:
    """Dictionary-like and index-accessible wrapper for PostgreSQL result rows"""
    def __init__(self, data_dict, data_tuple):
        self._dict = data_dict
        self._tuple = data_tuple

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._tuple[key]
        return self._dict[key]

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def __iter__(self):
        return iter(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def __repr__(self):
        return f"<Row {self._dict}>"

def translate_query(query, to_postgres=False):
    """Translates SQL syntax between SQLite and PostgreSQL where needed."""
    if not to_postgres:
        return query

    # Translate parameter placeholders ? -> %s
    parts = []
    in_single = False
    in_double = False
    for char in query:
        if char == "'" and not in_double:
            in_single = not in_single
            parts.append(char)
        elif char == '"' and not in_single:
            in_double = not in_double
            parts.append(char)
        elif char == '?' and not in_single and not in_double:
            parts.append('%s')
        else:
            parts.append(char)
    translated = ''.join(parts)
    return translated

class CursorWrapper:
    """Wraps cursor to provide consistent API (lastrowid, fetchone, fetchall, execute) across engines"""
    def __init__(self, cursor, is_pg=False, lastrowid=None):
        self.cursor = cursor
        self.is_pg = is_pg
        self.lastrowid = lastrowid

    def execute(self, query, params=None):
        translated_query = translate_query(query, to_postgres=self.is_pg)
        is_insert = translated_query.strip().upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in translated_query.upper()

        if self.is_pg and is_insert and not has_returning:
            translated_query = translated_query.rstrip().rstrip(';') + " RETURNING id;"

        if params:
            self.cursor.execute(translated_query, params)
        else:
            self.cursor.execute(translated_query)

        if self.is_pg:
            if is_insert:
                try:
                    res = self.cursor.fetchone()
                    if res:
                        self.lastrowid = res[0] if not isinstance(res, dict) else res.get('id')
                except Exception:
                    pass
        else:
            self.lastrowid = getattr(self.cursor, 'lastrowid', None)

        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if not self.is_pg:
            return row
        # PostgreSQL row conversion to RowWrapper
        if hasattr(self.cursor, 'description') and self.cursor.description:
            colnames = [d[0] for d in self.cursor.description]
            if isinstance(row, dict):
                data_dict = dict(row)
                data_tuple = tuple(data_dict.values())
            else:
                data_tuple = tuple(row)
                data_dict = {col: val for col, val in zip(colnames, data_tuple)}
            return RowWrapper(data_dict, data_tuple)
        return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not self.is_pg:
            return rows
        if hasattr(self.cursor, 'description') and self.cursor.description:
            colnames = [d[0] for d in self.cursor.description]
            wrapped = []
            for r in rows:
                if isinstance(r, dict):
                    data_dict = dict(r)
                    data_tuple = tuple(data_dict.values())
                else:
                    data_tuple = tuple(r)
                    data_dict = {col: val for col, val in zip(colnames, data_tuple)}
                wrapped.append(RowWrapper(data_dict, data_tuple))
            return wrapped
        return rows

    def __iter__(self):
        for row in self.fetchall():
            yield row

class DBConnection:
    """Unified DB connection wrapper supporting SQLite and PostgreSQL"""
    def __init__(self, raw_conn, is_pg=False):
        self.conn = raw_conn
        self.is_pg = is_pg

    def cursor(self):
        return CursorWrapper(self.conn.cursor(), is_pg=self.is_pg)

    def execute(self, query, params=None):
        c = self.cursor()
        c.execute(query, params)
        return c

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

def get_connection():
    """Returns a unified DBConnection object connected to PostgreSQL or SQLite"""
    if is_postgres():
        url = get_db_url()
        # Try psycopg2 first
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.DictCursor)
            return DBConnection(conn, is_pg=True)
        except ImportError:
            pass

        # Fallback to pg8000
        try:
            import pg8000
            parsed = urllib.parse.urlparse(url)
            conn = pg8000.connect(
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/')
            )
            return DBConnection(conn, is_pg=True)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL with psycopg2 and pg8000: {e}")

    # Default to SQLite
    conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return DBConnection(conn, is_pg=False)

def init_schema(db=None):
    """Initializes tables for SQLite or PostgreSQL if they do not exist"""
    should_close = False
    if db is None:
        db = get_connection()
        should_close = True

    is_pg = db.is_pg
    id_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "TEXT"

    queries = [
        # 1. Users Table
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_type},
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash {text_type} NOT NULL,
            full_name VARCHAR(255),
            email VARCHAR(255),
            role VARCHAR(50) DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        """,
        # 2. Enquiries Table
        f"""
        CREATE TABLE IF NOT EXISTS enquiries (
            id {id_type},
            name VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            subject VARCHAR(255) DEFAULT 'General Engineering Enquiry',
            service_category VARCHAR(100),
            message {text_type} NOT NULL,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'New'
        );
        """,
        # 3. Products Table
        f"""
        CREATE TABLE IF NOT EXISTS products (
            id {id_type},
            title VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL,
            category VARCHAR(100) NOT NULL,
            category_slug VARCHAR(100) NOT NULL,
            tag VARCHAR(100),
            summary {text_type},
            description {text_type},
            features {text_type},
            applications {text_type},
            image VARCHAR(255),
            video_url VARCHAR(255),
            is_featured INTEGER DEFAULT 0,
            is_published INTEGER DEFAULT 1,
            status_note VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # 4. Product Images Table
        f"""
        CREATE TABLE IF NOT EXISTS product_images (
            id {id_type},
            product_id INTEGER NOT NULL,
            image_path VARCHAR(255) NOT NULL,
            caption VARCHAR(255),
            is_primary INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # 5. Company Content Table
        f"""
        CREATE TABLE IF NOT EXISTS company_content (
            key_name VARCHAR(100) PRIMARY KEY,
            value {text_type},
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # 6. Gallery Table
        f"""
        CREATE TABLE IF NOT EXISTS gallery (
            id {id_type},
            title VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            file_type VARCHAR(50) DEFAULT 'image',
            file_path VARCHAR(255) NOT NULL,
            caption {text_type},
            is_published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # 7. Certificates Table
        f"""
        CREATE TABLE IF NOT EXISTS certificates (
            id {id_type},
            title VARCHAR(255) NOT NULL,
            cert_number VARCHAR(100),
            issuing_authority VARCHAR(255),
            issue_date VARCHAR(50),
            file_path VARCHAR(255) NOT NULL,
            description {text_type},
            is_published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # 8. News & Milestones Table
        f"""
        CREATE TABLE IF NOT EXISTS news_items (
            id {id_type},
            title VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            summary {text_type},
            content {text_type},
            date_display VARCHAR(50),
            image VARCHAR(255),
            is_real INTEGER DEFAULT 1,
            is_published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]

    for q in queries:
        db.execute(q)
    db.commit()

    if should_close:
        db.close()
