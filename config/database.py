
"""PostgreSQL connection factory using environment variables."""

import os
import psycopg


def get_connection():
    """Create and return a PostgreSQL connection."""

    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "DB_PASSWORD is not configured. "
            "Set your PostgreSQL password as an environment variable."
        )

    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "blood_bank_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=password,
        connect_timeout=5,
    )
