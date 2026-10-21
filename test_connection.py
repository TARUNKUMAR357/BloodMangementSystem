
from config.database import get_connection


def test_database():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), version()")
                result = cur.fetchone()

                print("Database connection successful!")
                print("Database:", result[0])
                print("PostgreSQL:", result[1])

    except Exception as error:
        print("Database connection failed.")
        print("Error:", error)


if __name__ == "__main__":
    test_database()
