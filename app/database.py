"""
Database connection and session management.
"""

import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Generator
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self):
        """Initialize database connection pool."""
        self.settings = get_settings()
        self.connection_string = self.settings.supabase_db_url
        self._pool = None
    
    def get_connection(self) -> psycopg.Connection:
        """Get a new database connection."""
        return psycopg.connect(
            self.connection_string,
            row_factory=dict_row,
            autocommit=False
        )
    
    @contextmanager
    def get_cursor(self) -> Generator[psycopg.Cursor, None, None]:
        """
        Context manager for database cursor with automatic commit/rollback.
        
        Usage:
            with db.get_cursor() as cur:
                cur.execute("SELECT * FROM users")
                results = cur.fetchall()
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    @contextmanager
    def transaction(self) -> Generator[psycopg.Cursor, None, None]:
        """
        Context manager for explicit transactions.
        
        Usage:
            with db.transaction() as cur:
                cur.execute("INSERT INTO ...")
                cur.execute("UPDATE ...")
                # Automatically commits at the end
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
                logger.debug("Transaction committed")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            conn.close()


# Singleton instance
_db: Database = None


def get_db() -> Database:
    """Get database instance (singleton)."""
    global _db
    if _db is None:
        _db = Database()
    return _db

