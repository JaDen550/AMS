# Firmware — ESP32 Attendance Device

## Setup

1. Install Arduino IDE, add ESP32 board support (Boards Manager → search "esp32").
2. Install libraries via Library Manager:
   - "Adafruit Fingerprint Sensor Library"
   - "ArduinoJson" (v6.x)
3. Copy `src/main.cpp` content into a `.ino` sketch (or open the folder
   directly if using an Arduino IDE version/plugin that supports .cpp sketches).
4. Edit `src/config.h`:
   - `WIFI_SSID` / `WIFI_PASSWORD`
   - `API_BASE_URL` — your dev laptop's LAN IP (not `localhost`), e.g. `http://192.168.1.42:5000`
   - `DEVICE_API_KEY` — you'll get this after registering the device (step 6 below)
5. Wire the AS608/R307 sensor to GPIO16 (RX2) / GPIO17 (TX2), power per module spec.
6. Flash the firmware, open Serial Monitor at 115200 baud, note the printed MAC address.
7. On the backend, register the device:
   ```
   POST /api/devices
   { "device_uid": "<the MAC address>", "label": "Main Gate Reader" }
   ```
   Copy the `api_key` from the response into `config.h`, then re-flash.
8. To enroll a fingerprint, type in Serial Monitor: `enroll 1` (or any unused ID),
   follow the two-scan prompts. Then call the enrollment endpoint from the admin
   panel/API to link that ID to a student:
   ```
   POST /api/students/{id}/enroll-fingerprint
   { "fingerprint_id": 1 }
   ```
9. From then on, placing that finger on the sensor sends attendance automatically.

## Offline behavior

If WiFi is down when a match happens, the record is written to a local
SPIFFS queue file (`/queue.jsonl`) instead of being lost. Every 30 seconds
the device checks connectivity and attempts to flush the queue in order,
oldest record first. Records are only removed from the queue once the
server confirms receipt (HTTP 201).

## Known Phase 1 limitations (by design, not bugs)

- No OLED/buzzer feedback yet — status is Serial-only. Add hardware
  feedback in a later phase once the core loop is proven.
- Battery percentage calculation is a placeholder linear map — needs the
  real formula once your electrical engineer friend finalizes the
  charge-controller/voltage-divider circuit.
- One device, one sensor. Multi-device support works at the API level
  already (`devices` table + per-device API key) but hasn't been tested
  with more than one unit yet.
