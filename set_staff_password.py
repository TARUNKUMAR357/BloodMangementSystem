
from getpass import getpass

from config.database import get_connection
from auth import hash_password


def main():
    username = input("Enter staff username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    password = getpass("Enter new password: ")
    confirmation = getpass("Confirm new password: ")

    if password != confirmation:
        print("Passwords do not match.")
        return

    if len(password) < 12:
        print("Use a password of at least 12 characters.")
        return

    password_hash = hash_password(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE staff
                    SET password_hash = %s
                    WHERE username = %s
                    RETURNING staff_id
                    """,
                    (password_hash, username)
                )

                result = cur.fetchone()

                if result is None:
                    print("No staff account found with that username.")
                    return

        print("Password updated successfully.")

    except Exception as error:
        print(f"Could not update password: {error}")


if __name__ == "__main__":
    main()
