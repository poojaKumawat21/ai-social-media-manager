from getpass import getpass
from app.database.supabase_auth import supabase_auth

email = input("Email: ")
password = getpass("Password: ")

try:
    response = supabase_auth.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    print("\nLOGIN SUCCESS")
    print("User ID:", response.user.id if response.user else None)
    print("Session:", bool(response.session))

except Exception as e:
    print("\nLOGIN FAILED")
    print("ERROR:", repr(e))