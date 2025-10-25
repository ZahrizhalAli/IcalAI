import psycopg
import os
import sys
import getpass

# --- !! EDIT THESE DETAILS !! ---
# Use your Mac username (from 'whoami')
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"


# ---------------------------------

def test_connection():
    """
    Attempts to connect to the PostgreSQL database and print its version.
    """
    try:
        # Prompt for password securely
        print(f"Attempting to connect to database '{DB_NAME}' on {DB_HOST}:{DB_PORT} as user '{DB_USER}'...")
        db_password = getpass.getpass(f"Enter password for user {DB_USER}: ")

        # Create the connection string
        conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' port='{DB_PORT}' password='{db_password}'"

        # Try to connect
        with psycopg.connect(conn_string) as conn:
            # If connection is successful, open a cursor
            with conn.cursor() as cur:
                # Execute a simple query to get the version
                cur.execute("SELECT * from test.newtablet;")

                # Fetch the result
                version = cur.fetchall()
                print(version)

                print("\n✅ --- CONNECTION SUCCESSFUL! --- ✅")
                print("\nPostgreSQL Version:")
                print(version[0])

    except psycopg.OperationalError as e:
        print("\n❌ --- CONNECTION FAILED! --- ❌")
        print("\nError details:")
        print(f"\n{e}")
        print("\n--- Common Fixes ---")
        print(f"1. Is the PostgreSQL server running? (Try 'brew services start postgresql')")
        print(f"2. Is the username '{DB_USER}' correct? (It should be your Mac username)")
        print(f"3. Did you type the correct password?")
        print(f"4. Is the database name '{DB_NAME}' correct?")
        sys.exit(1)  # Exit with an error code
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
