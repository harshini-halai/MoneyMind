import os
import tempfile
import threading
from pathlib import Path

from dotenv import load_dotenv
from mysql.connector import pooling

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_pool = None
_pool_lock = threading.Lock()
_pem_file = None


def _ca_file():
    """Path to the CA certificate used for an encrypted (TLS) connection.

    Hosted databases such as Aiven require TLS. Give the certificate in one of
    two ways:
      DB_SSL_CA      path to the .pem file (relative paths start at the project root)
      DB_SSL_CA_PEM  the certificate text itself (handy on hosts with no files)
    """
    global _pem_file

    pem_text = os.getenv("DB_SSL_CA_PEM", "").strip()
    if pem_text:
        if _pem_file is None:
            # Env var editors often turn real line breaks into a literal \\n.
            pem_text = pem_text.replace("\\n", "\n")
            handle = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
            handle.write(pem_text + "\n")
            handle.close()
            _pem_file = handle.name
        return _pem_file

    path = os.getenv("DB_SSL_CA", "").strip()
    if not path:
        return None

    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    if not candidate.is_file():
        raise RuntimeError(
            f"DB_SSL_CA points to {candidate}, but that file does not exist."
        )
    return str(candidate)


def connection_settings() -> dict:
    settings = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        # Every write in this app is a single statement, and autocommit stops
        # pooled connections from reusing a stale read snapshot.
        "autocommit": True,
        # Fail fast instead of hanging a web worker when the database is down.
        "connection_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
    }

    ca = _ca_file()
    if ca:
        settings["ssl_ca"] = ca
        settings["ssl_verify_cert"] = True

    return settings


def _get_pool():
    """Create the connection pool once, on first use."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pooling.MySQLConnectionPool(
                    pool_name="moneymind_pool",
                    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
                    **connection_settings(),
                )
    return _pool


def get_connection():
    """Return a pooled connection. Calling .close() gives it back to the pool."""
    return _get_pool().get_connection()