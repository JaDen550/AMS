/*
  Solar-Powered Biometric Attendance — ESP32 Firmware
  Phase 1: WiFi connect, fingerprint enroll + verify, offline queue + sync.

  Library dependencies (install via Arduino IDE Library Manager):
    - Adafruit Fingerprint Sensor Library
    - ArduinoJson (v6+)
  ESP32 board support installed via Boards Manager.

  Wiring (adjust to your module):
    AS608/R307 TX -> ESP32 RX2 (GPIO16)
    AS608/R307 RX -> ESP32 TX2 (GPIO17)
    AS608/R307 VCC -> 3.3V (check your module — some need 5V with a level shifter on data lines)
    AS608/R307 GND -> GND
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <HardwareSerial.h>
#include <Adafruit_Fingerprint.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <time.h>

#include "config.h"

HardwareSerial fingerSerial(2);
Adafruit_Fingerprint finger(&fingerSerial);

const char* QUEUE_FILE = "/queue.jsonl";  // one JSON record per line

// ---------------------------------------------------------------
// Setup
// ---------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=== Attendance Device Booting ===");
  Serial.print("MAC address (use as DEVICE_UID / device_uid): ");
  Serial.println(WiFi.macAddress());

  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS mount failed — offline queue will not work until this is fixed.");
  }

  connectWiFi();
  syncTime();
  initFingerprintSensor();

  Serial.println("Ready. Serial commands: 'enroll <id>' to enroll, otherwise the device");
  Serial.println("continuously scans for a matching fingerprint.");
}

// ---------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------
unsigned long lastSyncAttempt = 0;
const unsigned long SYNC_INTERVAL_MS = 30000; // try to flush queue every 30s

void loop() {
  handleSerialCommands();

  int matchedId = getFingerprintMatch();
  if (matchedId >= 0) {
    handleMatch(matchedId);
  }

  if (millis() - lastSyncAttempt > SYNC_INTERVAL_MS) {
    lastSyncAttempt = millis();
    if (WiFi.status() == WL_CONNECTED) {
      flushOfflineQueue();
    } else {
      Serial.println("WiFi down — attempting reconnect...");
      connectWiFi();
    }
  }

  delay(50);
}

// ---------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.printf("Connecting to WiFi \"%s\"...\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(300);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connect failed — will retry later. Continuing in offline mode.");
  }
}

void syncTime() {
  // NTP time is needed so `recorded_at` timestamps sent to the API are
  // meaningful even before the first successful sync.
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Syncing time");
  time_t now = time(nullptr);
  int attempts = 0;
  while (now < 8 * 3600 * 2 && attempts < 20) {
    delay(300);
    Serial.print(".");
    now = time(nullptr);
    attempts++;
  }
  Serial.println();
}

String isoTimestampNow() {
  time_t now = time(nullptr);
  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  char buf[30];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  return String(buf);
}

// ---------------------------------------------------------------
// Fingerprint sensor
// ---------------------------------------------------------------
void initFingerprintSensor() {
  fingerSerial.begin(57600, SERIAL_8N1, FINGERPRINT_RX_PIN, FINGERPRINT_TX_PIN);
  finger.begin(57600);

  if (finger.verifyPassword()) {
    Serial.println("Fingerprint sensor found and ready.");
  } else {
    Serial.println("Fingerprint sensor NOT found — check wiring/power. Halting sensor features.");
  }
}

// Returns matched fingerprint template ID, or -1 if no finger / no match.
int getFingerprintMatch() {
  uint8_t p = finger.getImage();
  if (p != FINGERPRINT_OK) return -1;

  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return -1;

  p = finger.fingerSearch();
  if (p != FINGERPRINT_OK) {
    Serial.println("Finger detected but no match found.");
    return -1;
  }

  return finger.fingerID;
}

// Enrolls a new fingerprint into the given template slot (1..N depending
// on sensor capacity, typically up to 127 or 1000 depending on module).
// This ID is what gets stored as `fingerprint_id` on the Student record
// via the admin panel's enrollment wizard.
bool enrollFingerprint(uint16_t id) {
  Serial.printf("Enrolling fingerprint into slot %d. Place finger...\n", id);

  int p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) {
      Serial.println("Image captured.");
    } else if (p == FINGERPRINT_NOFINGER) {
      delay(100);
    } else {
      Serial.println("Error capturing image.");
      return false;
    }
  }

  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) {
    Serial.println("Failed to process first image.");
    return false;
  }

  Serial.println("Remove finger.");
  delay(2000);
  p = 0;
  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
    delay(50);
  }

  Serial.println("Place same finger again...");
  p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) {
      Serial.println("Image captured.");
    } else if (p == FINGERPRINT_NOFINGER) {
      delay(100);
    } else {
      Serial.println("Error capturing second image.");
      return false;
    }
  }

  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) {
    Serial.println("Failed to process second image.");
    return false;
  }

  p = finger.createModel();
  if (p != FINGERPRINT_OK) {
    Serial.println("Failed to create model — the two scans didn't match well enough. Try again.");
    return false;
  }

  p = finger.storeModel(id);
  if (p != FINGERPRINT_OK) {
    Serial.println("Failed to store model on sensor.");
    return false;
  }

  Serial.printf("Enrollment successful. fingerprint_id = %d\n", id);
  Serial.println("Now assign this fingerprint_id to the student via the admin panel's");
  Serial.println("'Register Student Fingerprint' action (POST /api/students/{id}/enroll-fingerprint).");
  return true;
}

// ---------------------------------------------------------------
// Serial command handling (dev/enrollment convenience — a proper
// enrollment UI, e.g. via OLED + buttons, is a Phase 2/3 nicety)
// ---------------------------------------------------------------
void handleSerialCommands() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.startsWith("enroll ")) {
    int id = line.substring(7).toInt();
    if (id <= 0) {
      Serial.println("Usage: enroll <positive integer id>");
      return;
    }
    enrollFingerprint((uint16_t)id);
  } else if (line == "status") {
    Serial.printf("WiFi: %s | Queued records: %d\n",
                   WiFi.status() == WL_CONNECTED ? "connected" : "disconnected",
                   countQueuedRecords());
  }
}

// ---------------------------------------------------------------
// Attendance submission + offline queue
// ---------------------------------------------------------------
int getBatteryPercentage() {
  // Placeholder linear mapping — replace with the real formula for your
  // charge controller/voltage divider once the electrical side is built.
  int raw = analogRead(BATTERY_ADC_PIN);
  int pct = map(raw, 0, 4095, 0, 100);
  return constrain(pct, 0, 100);
}

void handleMatch(int fingerprintId) {
  Serial.printf("Match found: fingerprint_id = %d\n", fingerprintId);

  StaticJsonDocument<256> doc;
  doc["fingerprint_id"] = fingerprintId;
  doc["recorded_at"] = isoTimestampNow();
  doc["battery_percentage"] = getBatteryPercentage();

  if (WiFi.status() == WL_CONNECTED) {
    doc["synced_offline"] = false;
    doc["network_status"] = "online";
    String payload;
    serializeJson(doc, payload);

    if (!postAttendance(payload)) {
      // Send failed even though WiFi looked connected (e.g. server down) —
      // fall back to queueing so the record isn't lost.
      queueRecord(doc);
    }
  } else {
    doc["synced_offline"] = true;
    doc["network_status"] = "offline_queued";
    queueRecord(doc);
  }
}

bool postAttendance(const String& jsonPayload) {
  HTTPClient http;
  http.begin(String(API_BASE_URL) + "/api/attendance");
  http.addHeader("Content-Type", "application/json");
  http.addHeader(DEVICE_API_KEY_HEADER_NAME(), DEVICE_API_KEY);

  int httpCode = http.POST(jsonPayload);
  bool success = (httpCode == 201);

  if (success) {
    Serial.println("Attendance sent successfully.");
  } else {
    Serial.printf("Attendance POST failed, HTTP code: %d\n", httpCode);
  }

  http.end();
  return success;
}

// Kept as a function (not a #define) in case you want to make the header
// name configurable per-device later without touching every call site.
const char* DEVICE_API_KEY_HEADER_NAME() {
  return "X-Device-Key";
}

void queueRecord(const JsonDocument& doc) {
  if (countQueuedRecords() >= MAX_QUEUED_RECORDS) {
    Serial.println("Offline queue full — dropping oldest record to make room.");
    dropOldestQueuedRecord();
  }

  File f = SPIFFS.open(QUEUE_FILE, FILE_APPEND);
  if (!f) {
    Serial.println("Failed to open queue file for writing.");
    return;
  }
  String line;
  serializeJson(doc, line);
  f.println(line);
  f.close();
  Serial.println("Record queued offline (will sync when connection returns).");
}

int countQueuedRecords() {
  if (!SPIFFS.exists(QUEUE_FILE)) return 0;
  File f = SPIFFS.open(QUEUE_FILE, FILE_READ);
  int count = 0;
  while (f.available()) {
    if (f.readStringUntil('\n').length() > 0) count++;
  }
  f.close();
  return count;
}

void dropOldestQueuedRecord() {
  if (!SPIFFS.exists(QUEUE_FILE)) return;
  File src = SPIFFS.open(QUEUE_FILE, FILE_READ);
  String rest = "";
  bool skippedFirst = false;
  while (src.available()) {
    String line = src.readStringUntil('\n');
    if (!skippedFirst && line.length() > 0) {
      skippedFirst = true;
      continue; // drop this one
    }
    if (line.length() > 0) rest += line + "\n";
  }
  src.close();

  File dst = SPIFFS.open(QUEUE_FILE, FILE_WRITE);
  dst.print(rest);
  dst.close();
}

void flushOfflineQueue() {
  if (!SPIFFS.exists(QUEUE_FILE)) return;

  File f = SPIFFS.open(QUEUE_FILE, FILE_READ);
  if (!f || f.size() == 0) {
    if (f) f.close();
    return;
  }

  Serial.printf("Attempting to sync %d queued record(s)...\n", countQueuedRecords());

  String remaining = "";
  bool allSucceeded = true;

  while (f.available()) {
    String line = f.readStringUntil('\n');
    if (line.length() == 0) continue;

    if (allSucceeded && postAttendance(line)) {
      // sent successfully, don't keep it
      continue;
    } else {
      // either this one failed, or we already stopped trying this round —
      // keep everything from here on to preserve order and avoid gaps
      allSucceeded = false;
      remaining += line + "\n";
    }
  }
  f.close();

  File out = SPIFFS.open(QUEUE_FILE, FILE_WRITE);
  out.print(remaining);
  out.close();

  if (allSucceeded) {
    Serial.println("Offline queue fully synced.");
  } else {
    Serial.println("Some records still queued — will retry next cycle.");
  }
}
