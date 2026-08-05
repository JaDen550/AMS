#ifndef CONFIG_H
#define CONFIG_H

// ---- WiFi ----
#define WIFI_SSID     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// ---- Backend API ----
// During development this is your laptop's IP on the same WiFi network,
// e.g. "http://192.168.1.42:5000". Find it with `ipconfig` on Windows.
// This is NOT localhost/127.0.0.1 — the ESP32 is a separate device on
// the network and can't resolve "localhost" as your laptop.
#define API_BASE_URL  "http://192.168.1.42:5000"

// Copy this from the response of POST /api/devices when you register
// this unit from the admin panel. Keep it secret — treat it like a password.
#define DEVICE_API_KEY "PASTE_DEVICE_API_KEY_HERE"

// Unique ID for this physical unit — use the ESP32's own MAC address,
// printed to Serial on first boot (see main.cpp setup()).
#define DEVICE_UID "ESP32-DEVICE-01"

// ---- Fingerprint sensor (AS608 / R307) ----
// Connected via UART2 on the ESP32 (adjust pins to your wiring).
#define FINGERPRINT_RX_PIN 16
#define FINGERPRINT_TX_PIN 17

// ---- Offline queue ----
// Max records buffered in SPIFFS while offline before oldest is dropped.
#define MAX_QUEUED_RECORDS 200

// ---- Battery / solar monitoring (optional ADC pin) ----
#define BATTERY_ADC_PIN 34

#endif
