"""
Database connection — Phase 11.

Uses Neon (free-tier hosted Postgres, no card, no local install).
Connection string comes from .env, never hardcoded.
"""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL must be set in .env")
    return psycopg.connect(database_url)