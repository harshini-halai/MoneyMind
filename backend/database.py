import os
import threading

from dotenv import load_dotenv
from mysql.connector import pooling

load_dotenv()

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    """Create the connection pool once, on first use."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pooling.MySQLConnectionPool(
                    pool_name="moneymind_pool",
                    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", "3306")),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    database=os.getenv("DB_NAME"),
                    # Every write in this app is a single statement, and
                    # autocommit stops pooled connections from reusing a stale
                    # read snapshot between requests.
                    autocommit=True,
                )
    return _pool


def get_connection():
    """Return a pooled connection. Calling .close() gives it back to the pool."""
    return _get_pool().get_connection()