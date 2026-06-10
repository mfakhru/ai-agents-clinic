#!/usr/bin/env python3
"""Verify the database has 20 clinic services with embeddings."""

import os
import sys
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DB_PATH = os.environ.get('DB_PATH', str(Path(__file__).parent.parent / 'database' / 'clinic.db'))

EXPECTED_COUNT = 20


def verify_database():
    """Check that clinic services exist with embeddings."""
    db_path = Path(DB_PATH)

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM clinic_services")
        service_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM clinic_services WHERE description_embedding IS NOT NULL")
        embedding_count = cursor.fetchone()[0]

        print(f"Clinic Services: {service_count}/{EXPECTED_COUNT}")
        print(f"Embeddings:      {embedding_count}/{EXPECTED_COUNT}")

        conn.close()

        if service_count == EXPECTED_COUNT and embedding_count == EXPECTED_COUNT:
            print("\n[OK] Database ready!")
            return True
        else:
            print("\n[FAIL] Database not ready")
            return False

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
