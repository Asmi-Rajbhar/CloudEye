import sqlite3

# Connect to SQLite database (creates cloudburst.db if it doesn’t exist)
conn = sqlite3.connect("cloudburst.db")

# Create a cursor object
cursor = conn.cursor()

# Create UserData table
cursor.execute('''
CREATE TABLE IF NOT EXISTS UserData (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL,
    EmailId TEXT NOT NULL UNIQUE,
    City TEXT NOT NULL,
    Address TEXT NOT NULL,
    Latitude REAL NOT NULL,
    Longitude REAL NOT NULL
)
''')

# Commit and close connection
conn.commit()
conn.close()

print("Database 'cloudburst.db' and table 'UserData' created successfully!")
