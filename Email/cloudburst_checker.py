import psycopg2  # Use psycopg2 instead of sqlite3
import requests
import smtplib
from email.mime.text import MIMEText
import time
import os

# PostgreSQL Database Connection Details
DB_HOST = "localhost"
DB_NAME = "cloudburst"
DB_USER = "postgres"
DB_PASSWORD = "0713"  

# Function to fetch users from PostgreSQL
def fetch_users():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute('SELECT "Username", "EmailId", "City" FROM "UserData"')  # Updated column names
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        print(f"Database connection failed: {e}")
        return []

# Function to check weather data
def check_weather(city):
    api_key = "f4fb60c4cf28d30ba8661272f0a35341"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error fetching data from OpenWeather: {response.json().get('message')}")

    data = response.json()
    print(f"Raw weather data for {city}: {data}")  # Debugging line
    precipitation = data.get('rain', {}).get('1h', 0)

    if 'rain' not in data:
        print(f"No rain data available for {city}.")  # Log when there's no rain data

    return precipitation

# Function to send email notification
def send_email(to_email, city, precipitation):
    from_email = "corridorinfinity@gmail.com"
    app_password = "hsif zkvo lfil lgoi"  # Use your app password here
    subject = f"Cloudburst Alert for {city}"
    body = f"A cloudburst has been detected in {city}. Precipitation: {precipitation} mm."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, app_password)
            server.sendmail(from_email, to_email, msg.as_string())
            print(f"Email sent to {to_email}!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Main function to check for cloudbursts
def main():
    print("Fetching users from the database...")
    users = fetch_users()
    print(f"Found {len(users)} users.")

    for username, email, city in users:
        print(f"Checking weather data for {city}...")
        precipitation = check_weather(city)
        
        if precipitation > 0:  # Change this threshold as needed
            print(f" Cloudburst detected for {city}. Precipitation: {precipitation} mm")
            send_email(email, city, precipitation)
        else:
            print(f"No cloudburst detected for {city}. Precipitation: {precipitation} mm")

    print("Finished checking all users.")

# Run the main function every 10 minutes
if __name__ == "__main__":
    while True:
        main()
        time.sleep(120)  # Wait for 10 minutes before checking again
