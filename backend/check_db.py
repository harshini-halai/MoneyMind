"""Check the database connection and explain any problem in plain words.

Run from the project root (on your computer or the hosting shell):
    python -m backend.check_db
"""

import sys

from backend import database

EXPECTED_TABLES = [
    "users", "transactions", "savings", "emergency_fund",
    "upcoming_expenses", "budgets", "goals", "category_memory",
]

HINTS = {
    2007: (
        "The host and port answered, but not like a MySQL server. DB_HOST or DB_PORT is "
        "probably wrong. In Aiven open your MySQL service -> Overview -> Connection "
        "information and copy the Host and Port exactly. DB_HOST must be only the host "
        "name (no mysql://, no :port)."
    ),
    2003: (
        "Could not reach the server. Check DB_HOST and DB_PORT for typos. In Aiven also "
        "check 'Allowed IP addresses' on the service: your app's address must be allowed."
    ),
    2005: "The host name was not found. Check DB_HOST for typos.",
    1045: "Wrong user name or password. Copy DB_USER and DB_PASSWORD from Aiven (user is usually avnadmin).",
    1049: "That database does not exist. On Aiven the default database is called defaultdb: set DB_NAME=defaultdb.",
    3159: "The server only accepts encrypted connections. Set DB_SSL_CA (or DB_SSL_CA_PEM) to the Aiven CA certificate.",
    2026: "The encrypted (TLS) handshake failed. Check that DB_SSL_CA / DB_SSL_CA_PEM holds the CA certificate downloaded from Aiven.",
}


def main() -> int:
    try:
        settings = database.connection_settings()
    except RuntimeError as error:
        print(f"Configuration problem: {error}")
        return 1

    print("Trying to connect with:")
    print(f"  host     = {settings['host']}")
    print(f"  port     = {settings['port']}")
    print(f"  user     = {settings['user']}")
    print(f"  database = {settings['database']}")
    print(f"  password = {'(set)' if settings['password'] else '(EMPTY)'}")
    print(f"  TLS CA   = {settings.get('ssl_ca', '(not set)')}")
    print()

    try:
        connection = database.get_connection()
    except Exception as error:
        print(f"FAILED: {error}")
        hint = HINTS.get(getattr(error, "errno", None))
        if hint:
            print(f"\nWhat this usually means: {hint}")
        return 1

    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    print(f"Connected. Server version: {cursor.fetchone()[0]}")

    cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
    row = cursor.fetchone()
    print(f"Encrypted connection: {'yes' if row and row[1] else 'NO'}")

    cursor.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"
    )
    found = {name for (name,) in cursor.fetchall()}
    missing = [name for name in EXPECTED_TABLES if name not in found]
    if missing:
        print(f"Tables missing: {', '.join(missing)}")
        print("Run schema.sql on this database (see the README).")
    else:
        print("All MoneyMind tables exist.")

    cursor.close()
    connection.close()
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())