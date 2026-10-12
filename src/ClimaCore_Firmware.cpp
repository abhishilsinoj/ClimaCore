#include <Arduino.h>
#include "DHT.h"

// Pin definitions
#define DHTPIN 3      // Grove DHT22 data pin
#define DHTTYPE DHT22 // Sensor model
#define IRPIN 2       // IR Break-Beam receiver digital pin
#define LDRPIN A0     // LDR analogue pin
#define LEDPIN 13     // Onboard LED mirrors occupancy state

// Sensor objects
DHT dht(DHTPIN, DHTTYPE);

// Timing: non-blocking serial upload
unsigned long previousMillis = 0;
const long UPLOAD_INTERVAL = 2000; // 2 seconds for responsive dashboard

// Occupancy latching
unsigned long lastMotionTime = 0;
const long OCCUPANCY_COOLDOWN = 15000; // 15 seconds
int currentOccupancy = 0;              // 0 = empty, 1 = occupied

// LDR moving-average filter
const int NUM_READINGS = 10;
int ldrReadings[NUM_READINGS];
int readIndex = 0;
int ldrTotal = 0;
int ldrAverage = 0;

void setup()
{
    Serial.begin(115200);
    dht.begin();
    pinMode(IRPIN, INPUT);
    pinMode(LEDPIN, OUTPUT);

    for (int i = 0; i < NUM_READINGS; i++)
    {
        ldrReadings[i] = 0;
    }
}

void loop()
{
    unsigned long currentMillis = millis();

    // Hardware LDR reading integrated with FIR Moving Average (SMA-10)
    ldrTotal -= ldrReadings[readIndex];
    ldrReadings[readIndex] = analogRead(LDRPIN); // Reads raw illuminance
    ldrTotal += ldrReadings[readIndex];
    readIndex = (readIndex + 1) % NUM_READINGS;
    ldrAverage = ldrTotal / NUM_READINGS;

    // IR Break-Beam occupancy
    if (digitalRead(IRPIN) == HIGH)
    {
        lastMotionTime = currentMillis;
        currentOccupancy = 1;
        digitalWrite(LEDPIN, HIGH);
    }

    if (currentOccupancy == 1 && (currentMillis - lastMotionTime >= OCCUPANCY_COOLDOWN))
    {
        currentOccupancy = 0;
        digitalWrite(LEDPIN, LOW);
    }

    // Serial transmit
    if (currentMillis - previousMillis >= UPLOAD_INTERVAL)
    {
        previousMillis = currentMillis;

        float humidity = dht.readHumidity();
        float temperature = dht.readTemperature();

        if (isnan(humidity) || isnan(temperature))
        {
            Serial.println("Error: Check DHT Sensor Wiring on Pin 3!");
            return;
        }

        // Serial output for Python Streamlit
        // Format: temperature, humidity, ldrAverage, currentOccupancy
        Serial.print(temperature, 1);
        Serial.print(",");
        Serial.print(humidity, 1);
        Serial.print(",");
        Serial.print(ldrAverage);
        Serial.print(",");
        Serial.println(currentOccupancy);
    }
}