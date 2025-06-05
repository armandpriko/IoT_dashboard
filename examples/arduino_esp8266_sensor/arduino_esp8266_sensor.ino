/*
 * Weather Dashboard IoT Device Sensor for ESP8266/ESP32
 * 
 * This sketch connects to WiFi and sends temperature/humidity data 
 * to the Weather Dashboard API at regular intervals.
 * 
 * Hardware:
 * - ESP8266 or ESP32 board
 * - DHT22 or DHT11 temperature/humidity sensor
 * 
 * Libraries required:
 * - ESP8266WiFi.h or WiFi.h (ESP32)
 * - ESP8266HTTPClient.h or HTTPClient.h (ESP32)
 * - ArduinoJson
 * - DHT sensor library
 * 
 * Install libraries via Arduino IDE:
 * Sketch > Include Library > Manage Libraries...
 */

#include <Arduino.h>

// Choose the correct WiFi library based on your board
#ifdef ESP32
  #include <WiFi.h>
  #include <HTTPClient.h>
#else
  #include <ESP8266WiFi.h>
  #include <ESP8266HTTPClient.h>
#endif

#include <ArduinoJson.h>
#include <DHT.h>
#include <time.h>

// WiFi credentials - Replace with your actual WiFi details
const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";

// Weather Dashboard API details
const char* apiUrl = "http://your-server-ip:5000/api/data";
const char* apiKey = "your_api_key_here";

// DHT sensor configuration
#define DHTPIN 2       // Pin connected to the DHT sensor
#define DHTTYPE DHT22  // DHT 22 (or DHT11)
DHT dht(DHTPIN, DHTTYPE);

// Timing
const unsigned long INTERVAL = 300000;  // 5 minutes in milliseconds
unsigned long previousMillis = 0;

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\nWeather Dashboard IoT Device Sensor");
  Serial.println("-----------------------------------");
  
  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT sensor initialized");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Configure time if needed
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Check if it's time to send data
  if (currentMillis - previousMillis >= INTERVAL) {
    previousMillis = currentMillis;
    
    // Only proceed if WiFi is connected
    if (WiFi.status() == WL_CONNECTED) {
      // Read sensor data
      float temperature = dht.readTemperature();  // Read temperature in Celsius
      float humidity = dht.readHumidity();        // Read humidity

      // Check if readings are valid
      if (isnan(temperature) || isnan(humidity)) {
        Serial.println("Failed to read from DHT sensor!");
        return;
      }

      Serial.print("Temperature: ");
      Serial.print(temperature);
      Serial.print("°C, Humidity: ");
      Serial.print(humidity);
      Serial.println("%");

      // Send data to the API
      sendSensorData(temperature, humidity);
    } else {
      Serial.println("WiFi not connected");
    }
  }
}

void sendSensorData(float temperature, float humidity) {
  HTTPClient http;

  // Configure the request
  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");

  // Create JSON payload
  StaticJsonDocument<200> jsonDoc;
  jsonDoc["api_key"] = apiKey;
  jsonDoc["temperature"] = temperature;
  jsonDoc["humidity"] = humidity;
  
  // Get current timestamp (ESP will use the configured time)
  time_t now;
  time(&now);
  char timestamp[24];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", localtime(&now));
  jsonDoc["timestamp"] = timestamp;

  // Serialize JSON to string
  String jsonString;
  serializeJson(jsonDoc, jsonString);

  // Send the request
  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode == 200) {
    Serial.println("Data sent successfully");
  } else {
    Serial.print("Error sending data. HTTP response code: ");
    Serial.println(httpResponseCode);
    Serial.println(http.getString());
  }

  // Free resources
  http.end();
}
