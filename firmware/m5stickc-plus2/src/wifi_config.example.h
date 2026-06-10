```cpp
#pragma once

// ============================================================
// MotionBlocks — Wi-Fi configuration example
//
// Copy this file:
//
//   wifi_config.example.h
//
// to:
//
//   wifi_config.h
//
// Then fill in your real Wi-Fi credentials.
//
// IMPORTANT:
//   wifi_config.h must not be committed to Git.
// ============================================================


// Wi-Fi network name.
#define WIFI_SSID "YOUR_WIFI_NAME"

// Wi-Fi password.
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// HTTP logger endpoint.
//
// Example:
//
//   Python logger runs on notebook:
//     python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
//
//   Notebook Wi-Fi IP:
//     192.168.8.129
//
//   Then LOGGER_URL should be:
//
#define LOGGER_URL "http://192.168.8.129:8080/line"
```
