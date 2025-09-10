# In postgres.py
import psycopg2
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os

load_dotenv()

class NeonDB:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        self.conn = psycopg2.connect(
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            dbname=os.getenv("PGDATABASE"),
        )
        self.conn.autocommit = True

    def get_user_activated(self, username: str) -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    enabled
                FROM "authorized".authorized_users
                WHERE user_id = %s
                """, (username,))
            row = cursor.fetchone()
            if row:
                return True
            else:
                return False
    def get_repo_activated(self, repo: str) -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    enabled
                FROM "authorized".authorized_users
                WHERE username_repo = %s
                """, (repo,))
            row = cursor.fetchone()
            if row:
                return True
            else:
                return False
