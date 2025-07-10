from dotenv import load_dotenv
import os
import psycopg2
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import os
import joblib
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

load_dotenv()

# PostgreSQL Database Connection Details
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'database': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD")
}

# Load the trained model
model = joblib.load("realtimecloudburstmodel.joblib")

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(max(0, min(1, a))), sqrt(max(0, min(1, 1-a))))
    
    return R * c

def get_nearby_places(lat, lon, radius=3000):
    """Get nearby schools and organizations using OpenStreetMap"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query for schools and important buildings with address details
    overpass_query = f"""
    [out:json][timeout:25];
    (
      way(around:{radius},{lat},{lon})["amenity"~"school|college|university|hospital|community_centre|police|fire_station"];
      node(around:{radius},{lat},{lon})["amenity"~"school|college|university|hospital|community_centre|police|fire_station"];
    );
    out body;
    >;
    out skel qt;
    """
    
    try:
        response = requests.post(overpass_url, data=overpass_query)
        data = response.json()
        
        places = []
        for element in data.get('elements', []):
            if 'tags' in element:
                name = element['tags'].get('name')
                amenity = element['tags'].get('amenity')
                
                # Get detailed address information
                street = element['tags'].get('addr:street', '')
                housenumber = element['tags'].get('addr:housenumber', '')
                postcode = element['tags'].get('addr:postcode', '')
                city = element['tags'].get('addr:city', '')
                district = element['tags'].get('addr:district', '')
                
                if name:
                    # Construct detailed address
                    address_parts = []
                    if housenumber and street:
                        address_parts.append(f"{housenumber}, {street}")
                    elif street:
                        address_parts.append(street)
                    if district:
                        address_parts.append(district)
                    if city:
                        address_parts.append(city)
                    if postcode:
                        address_parts.append(postcode)
                    
                    # Get phone number if available
                    phone = element['tags'].get('phone', '')
                    
                    # Format the place information
                    place_info = f"{name} ({amenity})"
                    if address_parts:
                        place_info += f"\n      Address: {', '.join(address_parts)}"
                    if phone:
                        place_info += f"\n      Phone: {phone}"
                    
                    # Add coordinates for navigation
                    if 'lat' in element and 'lon' in element:
                        place_info += f"\n      Coordinates: ({element['lat']:.6f}, {element['lon']:.6f})"
                    
                    places.append(place_info)
        
        return places[:5]  # Return top 5 places with detailed information
    except Exception as e:
        print(f"Error fetching nearby places: {e}")
        return []

def find_safe_locations(current_lat, current_lon, radius_km=40):
    """Find safe locations by checking actual weather in surrounding areas"""
    try:
        # Create a grid of points around the current location
        safe_locations = []
        seen_locations = set()  # Track unique locations
        
        # Create a larger grid with smaller steps for more precise locations
        steps = [-0.15, -0.1, -0.05, 0, 0.05, 0.1, 0.15]
        
        # Convert string coordinates to float
        current_lat = float(current_lat)
        current_lon = float(current_lon)
        
        for lat_offset in steps:
            for lon_offset in steps:
                check_lat = current_lat + lat_offset
                check_lon = current_lon + lon_offset
                
                # Skip the current location
                if lat_offset == 0 and lon_offset == 0:
                    continue
                
                try:
                    # Calculate distance
                    distance = calculate_distance(current_lat, current_lon, check_lat, check_lon)
                    if distance <= radius_km:
                        # Check actual weather at this location
                        prediction, precip, weather = check_weather(check_lat, check_lon, "Checking Area")
                        
                        # Skip if we've already seen this location name
                        location_name = weather['location_name']
                        if location_name in seen_locations or location_name == "Unknown Location":
                            continue
                            
                        if prediction == 0 and precip < 5:  # Safe threshold
                            seen_locations.add(location_name)  # Add to seen locations
                            safe_locations.append({
                                'city': location_name,
                                'coordinates': f"({check_lat:.4f}, {check_lon:.4f})",
                                'address': f"Approximately {distance:.1f}km from your location",
                                'distance': round(distance, 2),
                                'weather': weather
                            })
                except Exception as e:
                    print(f"Error checking location ({check_lat}, {check_lon}): {e}")
                    continue
        
        # Sort by distance and take only unique locations
        return sorted(safe_locations, key=lambda x: x['distance'])[:5]
    except Exception as e:
        print(f"Error finding safe locations: {e}")
        return []

def format_safe_locations(safe_locations):
    """Format safe locations for email"""
    if not safe_locations:
        return "No safe locations found in your vicinity."
    
    locations_text = "\nSafe Locations Nearby:\n"
    for idx, loc in enumerate(safe_locations, 1):
        weather = loc['weather']
        lat, lon = map(float, loc['coordinates'].strip('()').split(','))
        nearby_places = get_nearby_places(lat, lon)
        
        locations_text += f"\n{idx}. {loc['city']}\n"
        locations_text += f"   Coordinates: {loc['coordinates']}\n"
        locations_text += f"   Distance: {loc['distance']} km\n"
        
        if nearby_places:
            locations_text += f"   Nearby Safe Places:\n"
            for place in nearby_places:
                locations_text += f"   {place}\n"
        
        locations_text += f"   Weather Conditions:\n"
        locations_text += f"   - Status: {weather['description']}\n"
        locations_text += f"   - Temperature: {weather['temperature']}C (Feels like: {weather['apparent_temperature']}C)\n"
        locations_text += f"   - Precipitation: {weather['precipitation']} mm/h\n"
        locations_text += f"   - Humidity: {weather['humidity']}%\n"
        locations_text += f"   - Pressure: {weather['pressure']} hPa\n"
        locations_text += f"   - Wind Speed: {weather['wind_speed']} m/s\n"
        locations_text += f"   - Cloud Cover: {weather['cloud_cover']}%\n"
    
    return locations_text

def check_weather(lat, lon, city):
    api_key = os.getenv("OPENWEATHER_API_KEY")

    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error fetching data from OpenWeather: {response.json().get('message')}")

    data = response.json()
    
    # Get location name from API response
    location_name = data.get('name', 'Unknown Location')

    # Extract main weather data
    main_data = data['main']
    weather_desc = data['weather'][0]['description'].title() if data['weather'] else "No description"
    
    weather_data = {
        "location_name": location_name,
        "precipitation": 0,  # Default to 0 if no rain data
        "apparent_temperature": main_data['feels_like'],
        "temperature": main_data['temp'],
        "cloud_cover": data['clouds']['all'],
        "wind_speed": data['wind']['speed'],
        "humidity": main_data['humidity'],
        "pressure": main_data['pressure'],
        "description": weather_desc
    }

    # Add rain if present
    if 'rain' in data:
        weather_data["precipitation"] = data['rain'].get('1h', 0)

    return 0, weather_data["precipitation"], weather_data

def fetch_users():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT "Username", "EmailId", "City", "Address", "Latitude", "Longitude" FROM "UserData"')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users
    except Exception as e:
        print(f"Database connection failed: {e}")
        return []

def send_email(to_email, city, address, precipitation, weather_data, safe_locations):
    from_email = os.getenv("EMAIL_SENDER")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    
    subject = "CLOUDBURST ALERT - Safe Locations Available"
    
    body = f"""Dear User,

CLOUDBURST ALERT for your location:
Location: {address}, {city}

⚠️ IMPORTANT SAFETY ADVISORY ⚠️
Please stay alert and take necessary precautions. Avoid flood-prone areas and stay indoors if possible.

Current Weather Conditions:
- Precipitation: {precipitation} mm/h
- Temperature: {weather_data['temperature']}°C (Feels like: {weather_data['apparent_temperature']}°C)
- Humidity: {weather_data['humidity']}%
- Wind Speed: {weather_data['wind_speed']} m/s
- Cloud Cover: {weather_data['cloud_cover']}%
- Pressure: {weather_data['pressure']} hPa
- Status: {weather_data['description']}

{format_safe_locations(safe_locations)}

Please move to one of these safe locations immediately if needed.

Emergency Helpline Numbers:
- National Emergency: 112
- NDMA Helpline: 1078
- Police: 100
- BMC Disaster Helpline: 1916

Stay safe and follow official updates. You can contact the Emergency Helpline numbers!

Best regards,
Cloudburst Alert System"""

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    # Create both plain text and HTML versions
    text_part = MIMEText(body, 'plain', 'utf-8')
    msg.attach(text_part)

    # Print email content to terminal first
    print("\n" + "="*50)
    print("SENDING EMAIL...")
    print("="*50)
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("-"*50)
    print(body)
    print("="*50)

    try:
        # Create SMTP connection with explicit timeout
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        
        # Debug mode on
        smtp_server.set_debuglevel(1)
        
        # Login
        print("Attempting to login...")
        smtp_server.login(from_email, app_password)
        
        # Send email
        print("Sending email...")
        smtp_server.send_message(msg)
        
        # Close connection
        smtp_server.quit()
        
        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError as auth_error:
        print(f"Authentication failed: Please check your email and app password")
        print(f"Error details: {auth_error}")
    except smtplib.SMTPException as smtp_error:
        print(f"SMTP error occurred: {smtp_error}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    print("Fetching users from the database...")
    users = fetch_users()
    print(f"Found {len(users)} users.")

    for username, email, city, address, lat, lon in users:
        print(f"\nChecking weather data for {city} at coordinates ({lat}, {lon})...")
        try:
            # Get actual weather data
            prediction, precipitation, weather_data = check_weather(lat, lon, city)
            
            # Check for cloudburst conditions
            is_cloudburst = False
            if username == "Om":  # Simulate cloudburst
                is_cloudburst = True
                print(f"\nSIMULATED: Cloudburst risk detected at your location!")
                
                # Get nearby places for user's location
                print("\nNearby Safe Places at Your Location:")
                user_nearby_places = get_nearby_places(float(lat), float(lon), radius=3000)
                if user_nearby_places:
                    for place in user_nearby_places:
                        print(f"- {place}")
                else:
                    print("No safe places found within 3km of your location")
                    
            elif precipitation >= 10 or prediction == 1:  # Real cloudburst detection
                is_cloudburst = True
                print(f"\nACTUAL: Cloudburst risk detected at your location!")
            
            if is_cloudburst:
                print(f"Location: {address}")
                print(f"Coordinates: ({lat}, {lon})")
                
                # Find safe locations by checking actual weather in surrounding areas
                print("\nChecking surrounding areas for safety...")
                safe_locations = find_safe_locations(lat, lon)
                
                if safe_locations:
                    print(f"\nFound {len(safe_locations)} safe areas nearby:")
                    for loc in safe_locations:
                        weather = loc['weather']
                        lat, lon = map(float, loc['coordinates'].strip('()').split(','))
                        nearby_places = get_nearby_places(lat, lon)
                        
                        print(f"\nSafe Zone: {loc['city']}")
                        print(f"   Coordinates: {loc['coordinates']}")
                        print(f"   Distance: {loc['distance']} km")
                        
                        if nearby_places:
                            print(f"   Nearby Safe Places:")
                            for place in nearby_places:
                                print(f"   - {place}")
                        
                        print(f"   Weather Conditions:")
                        print(f"   - Status: {weather['description']}")
                        print(f"   - Temperature: {weather['temperature']}°C (Feels like: {weather['apparent_temperature']}°C)")
                        print(f"   - Precipitation: {weather['precipitation']} mm/h")
                        print(f"   - Humidity: {weather['humidity']}%")
                        print(f"   - Pressure: {weather['pressure']} hPa")
                        print(f"   - Wind Speed: {weather['wind_speed']} m/s")
                        print(f"   - Cloud Cover: {weather['cloud_cover']}%")
                
                # Send email with current conditions and safe locations
                if username == "Om":  # For simulated cloudburst
                    simulated_weather = {
                        "precipitation": 15.0,
                        "temperature": 25.0,
                        "apparent_temperature": 27.0,
                        "cloud_cover": 90,
                        "wind_speed": 20,
                        "humidity": 95,
                        "pressure": 1013,
                        "description": "Heavy Rain"
                    }
                    send_email(email, city, address, 15.0, simulated_weather, safe_locations)
                else:  # For actual cloudburst
                    send_email(email, city, address, precipitation, weather_data, safe_locations)
            else:
                print(f"No cloudburst risk detected at {city}")
                
        except Exception as e:
            print(f"Error checking weather for {city}: {e}")
            
    print("\nFinished checking all locations.")

# Run the main function every 2 minutes
if __name__ == "__main__":
    while True:
        main()
        time.sleep(120)  # 2 minutes interval