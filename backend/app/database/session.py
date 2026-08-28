"""
Database Connection and Session Management for SQLite.
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
from backend.app.core.config import settings
from backend.app.core.logging import logger


def get_db_path() -> str:
    """Returns the absolute path to the SQLite database file."""
    # Ensure database directory exists
    db_file = settings.DATABASE_PATH
    if not os.path.isabs(db_file):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_file = os.path.join(base_dir, "sih_prototype.db")
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    return db_file


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a thread-safe SQLite connection configured
    with row factories and WAL mode.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        # Enable WAL mode for concurrency and foreign key enforcement
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction rolled back due to error: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Initializes the database schema if tables do not exist."""
    logger.info("Initializing SQLite database tables...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Projects Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT UNIQUE NOT NULL,
            project_name TEXT NOT NULL,
            project_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Project Assessments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT NOT NULL,
            project_type TEXT NOT NULL,
            land_area REAL NOT NULL,
            affected_families INTEGER NOT NULL,
            legal_disputes INTEGER NOT NULL,
            pending_approvals INTEGER NOT NULL,
            compensation_percent REAL NOT NULL,
            rr_progress_percent REAL NOT NULL,
            possession_percent REAL NOT NULL,
            delay_probability REAL NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_category TEXT NOT NULL,
            predicted_delay_days INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Assessment Risk Factors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            factor_name TEXT NOT NULL,
            impact_score INTEGER NOT NULL,
            direction TEXT,
            FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
        );
        """)

        # Assessment Recommendations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            priority TEXT NOT NULL,
            action_text TEXT NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
        );
        """)

        conn.commit()
        logger.info("Database schema initialized successfully.")
