import sqlite3

# Step 1: Create database and table
def create_database():
    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            aqi INTEGER,
            cough TEXT,
            wheezing TEXT,
            breathing TEXT,
            sneezing TEXT,
            dust TEXT
        )
    """)
    conn.commit()
    conn.close()


# Step 2: Register a new user with their symptoms
def register_user(username, password, age, aqi, cough, wheezing, breathing, sneezing, dust):
    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password, age, aqi, cough, wheezing, breathing, sneezing, dust)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password, age, aqi, cough, wheezing, breathing, sneezing, dust))
        conn.commit()
        print("Registered successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists. Try a different username.")
    conn.close()


# Step 3: Login check + fetch profile details
def login_user(username, password):
    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        print("\nLogin successful!")
        print("---- PROFILE DETAILS ----")
        print("Username        :", result[1])
        print("Age             :", result[3])
        print("AQI             :", result[4])
        print("Cough           :", result[5])
        print("Wheezing        :", result[6])
        print("Breathing       :", result[7])
        print("Sneezing        :", result[8])
        print("Dust Exposure   :", result[9])
    else:
        print("Login failed. Wrong username or password.")


# ---------- MAIN PROGRAM (for testing) ----------
if __name__ == "__main__":
    create_database()

    # Register a test user (run only once, comment out after first run)
    register_user("Janu", "1234", 25, 150, "Yes", "No", "Moderate", "Yes", "Yes")

    # Login test
    login_user("Janu", "1234")
    login_user("Janu", "wrong")