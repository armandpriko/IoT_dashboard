"""
Example script for IoT devices (Raspberry Pi, ESP8266, Arduino) to send weather data
to the Weather Dashboard API.

This script simulates temperature and humidity readings and sends them to the API
at regular intervals.

Usage:
1. Set the API_KEY variable to your device's API key
2. Set the API_URL to your server's URL
3. Run the script

Requirements:
- requests library (pip install requests)
"""

import requests
import random
import time
from datetime import datetime

# Configuration - Replace with your actual values
API_KEY = "your_api_key_here"
API_URL = "http://localhost:5000/api/data"
INTERVAL = 300  # Send data every 5 minutes (300 seconds)

def simulate_sensor_readings():
    """
    Simulate temperature and humidity readings.
    In a real device, replace this with actual sensor readings.
    """
    temperature = round(random.uniform(18.0, 28.0), 1)  # Temperature between 18-28°C
    humidity = round(random.uniform(30.0, 70.0), 1)     # Humidity between 30-70%
    
    return temperature, humidity

def send_data_to_api(temperature, humidity):
    """
    Send the sensor data to the Weather Dashboard API
    """
    # Prepare the data payload
    data = {
        "api_key": API_KEY,
        "temperature": temperature,
        "humidity": humidity,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Send the data via POST request
        response = requests.post(API_URL, json=data)
        
        # Check if request was successful
        if response.status_code == 200:
            print(f"✅ Data sent successfully: Temp={temperature}°C, Humidity={humidity}%")
            return True
        else:
            print(f"❌ Failed to send data: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error sending data: {str(e)}")
        return False

def main():
    """
    Main loop - continuously read sensors and send data
    """
    print("Weather Dashboard IoT Device Sensor Script")
    print("------------------------------------------")
    print(f"📡 API URL: {API_URL}")
    print(f"⏱️ Interval: {INTERVAL} seconds")
    print("Starting data collection loop...\n")
    
    while True:
        # Get sensor readings
        temperature, humidity = simulate_sensor_readings()
        
        # Send data to the API
        send_data_to_api(temperature, humidity)
        
        # Wait before next reading
        print(f"⏳ Waiting {INTERVAL} seconds until next reading...\n")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
