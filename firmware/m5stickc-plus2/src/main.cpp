#include <M5Unified.h>     // основная библиотека M5Stack/M5StickC: экран, кнопки, IMU
#include <WiFi.h>          // Wi-Fi подключение ESP32 к локальной сети
#include <HTTPClient.h>    // HTTP-клиент ESP32 для отправки POST-запросов на Python logger
#include "wifi_config.h"   // локальные Wi-Fi настройки: WIFI_SSID, WIFI_PASSWORD, LOGGER_URL
#include <math.h>          // нужна для sqrt при расчёте acc_norm
#include "freertos/FreeRTOS.h"  // FreeRTOS: очереди и задачи для async HTTP
#include "freertos/queue.h"
#include "freertos/task.h"


// ============================================================
// MotionBlocks — IMU logger v0.8.0
//
// Текущий этап:
// - session-aware IMU logger;
// - button-controlled recording;
// - selectable sampling rate at startup (все варианты видны на экране);
// - DEVICE_INFO event with MAC address and firmware version;
// - Serial output preserved for debugging / serial_logger.py;
// - Wi-Fi HTTP output to Python http_logger.py;
// - HTTP batch mode during active recording;
// - READY screen shows Wi-Fi status and selected sample rate;
// - REC screen shows Wi-Fi indicator;
// - SAVED screen after STOP (1 секунда подтверждения);
// - double-click window увеличен до 600 ms для удобства;
// - ASYNC HTTP: IMU и HTTP работают в разных задачах FreeRTOS;
//   IMU на ядре 0, HTTP на ядре 1, очередь между ними.
//
// Важно:
// - прошивка НЕ знает experiment_id;
// - прошивка НЕ знает project-level device_id;
// - прошивка НЕ знает subject_id;
// - прошивка НЕ знает movement_type / movement_label.
//
// Эти поля задаются на стороне Python logger / metadata.
// Прошивка сообщает только техническую идентичность устройства:
// MAC address and firmware version.
//
// Протокол:
//
// EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms
// EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms
// EVENT,NEW_SESSION,session_id,timestamp_ms
// EVENT,START,session_id,record_id,timestamp_ms
// DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
// EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
//
// Транспорт:
//
// 1. Serial
//    Все строки протокола печатаются в Serial.
//
// 2. HTTP one-shot
//    Служебные события в IDLE:
//    DEVICE_INFO, SAMPLE_RATE, NEW_SESSION.
//
// 3. HTTP batch mode during recording
//    START / STOP отправляются сразу.
//    DATA во время записи отправляются пачками до 25 строк
//    или не реже чем раз в 500 ms.
//    Перед STOP буфер DATA принудительно сбрасывается.
// ============================================================


// ------------------------------------------------------------
// Настройки записи
// ------------------------------------------------------------

static const char* FIRMWARE_VERSION = "motionblocks.logger.v0.8.0";

static const uint32_t SAMPLE_RATES_HZ[] = {5, 10, 25, 50, 100};
static const uint8_t SAMPLE_RATE_COUNT = sizeof(SAMPLE_RATES_HZ) / sizeof(SAMPLE_RATES_HZ[0]);
static const uint8_t DEFAULT_SAMPLE_RATE_INDEX = 1;  // 10 Hz

static const uint32_t SAMPLE_RATE_SELECT_TIMEOUT_MS = 5000;

uint32_t sample_rate_hz = SAMPLE_RATES_HZ[DEFAULT_SAMPLE_RATE_INDEX];
uint32_t sample_interval_ms = 1000 / sample_rate_hz;

// Увеличено с 400 до 600 ms — удобнее для детей.
static const uint32_t DOUBLE_CLICK_WINDOW_MS = 600;

// Длительность экрана SAVED после остановки записи.
static const uint32_t SAVED_SCREEN_MS = 1200;


// ------------------------------------------------------------
// Буфер для DATA строки
//
// Используем статический буфер вместо String concatenation
// чтобы снизить heap fragmentation на ESP32 при 100 Hz.
// ------------------------------------------------------------

static char data_line_buf[128];


// ------------------------------------------------------------
// Цвета
// ------------------------------------------------------------

static const uint16_t MB_BLACK    = BLACK;
static const uint16_t MB_WHITE    = WHITE;
static const uint16_t MB_GREEN    = GREEN;
static const uint16_t MB_RED      = RED;
static const uint16_t MB_GREY     = 0xC618;
static const uint16_t MB_DARKGREY = 0x7BEF;
static const uint16_t MB_YELLOW   = 0xFFE0;


// ------------------------------------------------------------
// Координаты layout
//
// Экран M5StickC Plus2 в landscape после setRotation(1):
// примерно 240 x 135.
// ------------------------------------------------------------

static const int SCREEN_W = 240;
static const int SCREEN_H = 135;

static const int RAIL_X = 5;
static const int MAIN_X = 34;


// ------------------------------------------------------------
// Состояние сессии / записи
// ------------------------------------------------------------

uint32_t session_number = 1;
uint32_t record_id      = 1;
uint32_t sample_id      = 0;
uint32_t sample_count   = 0;
bool     is_recording   = false;
uint32_t last_sample_ms = 0;
float    last_acc_norm  = 0.0f;

// Количество сэмплов последней завершённой записи.
// Показывается на экране SAVED.
uint32_t last_record_sample_count = 0;


// ------------------------------------------------------------
// Состояние кнопок
// ------------------------------------------------------------

uint32_t last_click_ms          = 0;
bool     waiting_for_second_click = false;


// ------------------------------------------------------------
// Формирование session_id
//
// session_number = 1  -> A001
// session_number = 15 -> A015
// ------------------------------------------------------------

void getSessionId(char* buffer, size_t buffer_size) {
    snprintf(buffer, buffer_size, "A%03lu", session_number);
}


// ------------------------------------------------------------
// Wi-Fi status
// ------------------------------------------------------------

bool isWifiOk() {
    return WiFi.status() == WL_CONNECTED;
}

String getWifiStatusText() {
    if (isWifiOk()) {
        return "WiFi " + WiFi.localIP().toString();
    }
    return "WiFi OFF";
}

String getDeviceMacAddress() {
    return WiFi.macAddress();
}


// ------------------------------------------------------------
// Экран: вертикальная надпись LOGGER
// ------------------------------------------------------------

void drawVerticalLoggerLabel() {
    M5.Display.setTextDatum(top_left);
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_GREY, MB_BLACK);

    int x    = RAIL_X;
    int y    = 8;
    int step = 20;

    M5.Display.drawString("L", x, y + step * 0);
    M5.Display.drawString("O", x, y + step * 1);
    M5.Display.drawString("G", x, y + step * 2);
    M5.Display.drawString("G", x, y + step * 3);
    M5.Display.drawString("E", x, y + step * 4);
    M5.Display.drawString("R", x, y + step * 5);
}


// ------------------------------------------------------------
// Экран заставки
// ------------------------------------------------------------

void showSplashScreen() {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(middle_center);

    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.setTextSize(2);
    M5.Display.drawString("MOTIONBLOCKS", SCREEN_W / 2, 36);

    M5.Display.setTextColor(MB_GREEN, MB_BLACK);
    M5.Display.setTextSize(3);
    M5.Display.drawString("LOGGER", SCREEN_W / 2, 72);

    M5.Display.setTextColor(MB_GREY, MB_BLACK);
    M5.Display.setTextSize(1);
    M5.Display.drawString("Stofendez Lab", SCREEN_W / 2, 110);

    delay(3000);

    M5.Display.setTextDatum(top_left);
}


// ------------------------------------------------------------
// Экран выбора частоты дискретизации
//
// Показываем все 5 вариантов.
// Текущий выбранный выделен зелёным и стрелкой.
// Остальные серые.
// Подсказки кнопок убраны — освобождают место для списка.
// Countdown показывается только в auto-mode.
// ------------------------------------------------------------

void drawSampleRateSelectionScreen(uint8_t selected_index, uint32_t remaining_ms) {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);

    drawVerticalLoggerLabel();

    // Заголовок
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.setTextSize(1);
    M5.Display.drawString("SAMPLE RATE", MAIN_X, 4);

    // Список всех вариантов.
    // Экран 135px высота, заголовок ~14px, countdown ~10px снизу.
    // Доступно ~111px на 5 строк → ~22px на строку.
    int list_y = 18;
    int row_h  = 22;

    for (uint8_t i = 0; i < SAMPLE_RATE_COUNT; i++) {
        int y = list_y + i * row_h;

        if (i == selected_index) {
            M5.Display.setTextColor(MB_GREEN, MB_BLACK);
            M5.Display.setTextSize(2);
            M5.Display.drawString("> " + String(SAMPLE_RATES_HZ[i]) + " Hz", MAIN_X, y);
        } else {
            M5.Display.setTextColor(MB_GREY, MB_BLACK);
            M5.Display.setTextSize(1);
            M5.Display.drawString("  " + String(SAMPLE_RATES_HZ[i]) + " Hz", MAIN_X + 8, y + 6);
        }
    }

    // Countdown только в auto-mode, внизу экрана
    if (remaining_ms > 0) {
        M5.Display.setTextSize(1);
        M5.Display.setTextColor(MB_GREY, MB_BLACK);
        M5.Display.drawString("auto in " + String((remaining_ms + 999) / 1000) + "s", MAIN_X, 126);
    }
}


// ------------------------------------------------------------
// Выбор частоты при старте
// ------------------------------------------------------------

void selectSampleRateAtStartup() {
    uint8_t selected_index = DEFAULT_SAMPLE_RATE_INDEX;

    uint32_t start_ms    = millis();
    uint32_t last_redraw_ms = 0;

    bool manual_selection_started = false;

    drawSampleRateSelectionScreen(selected_index, SAMPLE_RATE_SELECT_TIMEOUT_MS);

    while (true) {
        M5.update();

        uint32_t elapsed_ms   = millis() - start_ms;
        uint32_t remaining_ms = 0;

        if (!manual_selection_started && elapsed_ms < SAMPLE_RATE_SELECT_TIMEOUT_MS) {
            remaining_ms = SAMPLE_RATE_SELECT_TIMEOUT_MS - elapsed_ms;
        }

        if (M5.BtnA.wasClicked()) {
            manual_selection_started = true;
            selected_index = (selected_index + 1) % SAMPLE_RATE_COUNT;
            drawSampleRateSelectionScreen(selected_index, 0);
        }

        if (M5.BtnB.wasClicked()) {
            break;
        }

        if (!manual_selection_started && elapsed_ms >= SAMPLE_RATE_SELECT_TIMEOUT_MS) {
            break;
        }

        if (!manual_selection_started && millis() - last_redraw_ms > 1000) {
            last_redraw_ms = millis();
            drawSampleRateSelectionScreen(selected_index, remaining_ms);
        }

        delay(20);
    }

    sample_rate_hz      = SAMPLE_RATES_HZ[selected_index];
    sample_interval_ms  = 1000 / sample_rate_hz;

    Serial.print("Selected sample rate: ");
    Serial.print(sample_rate_hz);
    Serial.println(" Hz");

    // Подтверждение выбора
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);
    drawVerticalLoggerLabel();

    M5.Display.setTextColor(MB_GREEN, MB_BLACK);
    M5.Display.setTextSize(2);
    M5.Display.drawString("RATE OK", MAIN_X, 30);

    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.setTextSize(3);
    M5.Display.drawString(String(sample_rate_hz) + " Hz", MAIN_X, 70);

    delay(1000);
}


// ------------------------------------------------------------
// Экраны Wi-Fi
// ------------------------------------------------------------

void drawWifiConnectingScreen() {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);
    drawVerticalLoggerLabel();

    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.setTextSize(2);
    M5.Display.drawString("Wi-Fi", MAIN_X, 22);

    M5.Display.setTextSize(1);
    M5.Display.setTextColor(MB_GREY, MB_BLACK);
    M5.Display.drawString("Connecting...", MAIN_X, 58);
}

void drawWifiOkScreen() {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);
    drawVerticalLoggerLabel();

    M5.Display.setTextColor(MB_GREEN, MB_BLACK);
    M5.Display.setTextSize(2);
    M5.Display.drawString("Wi-Fi OK", MAIN_X, 22);

    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.setTextSize(1);
    M5.Display.drawString(WiFi.localIP().toString(), MAIN_X, 58);

    delay(2000);
}

void drawWifiFailScreen() {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);
    drawVerticalLoggerLabel();

    M5.Display.setTextColor(MB_RED, MB_BLACK);
    M5.Display.setTextSize(2);
    M5.Display.drawString("Wi-Fi FAIL", MAIN_X, 22);

    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.setTextSize(1);
    M5.Display.drawString("Check wifi_config.h", MAIN_X, 58);

    delay(3000);
}


// ------------------------------------------------------------
// Подключение к Wi-Fi
// ------------------------------------------------------------

void connectToWifi() {
    Serial.println();
    Serial.println("Connecting to Wi-Fi...");
    Serial.print("SSID: ");
    Serial.println(WIFI_SSID);

    drawWifiConnectingScreen();

    WiFi.disconnect(true);
    delay(500);

    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    uint32_t start_ms         = millis();
    const uint32_t timeout_ms = 15000;

    while (WiFi.status() != WL_CONNECTED && millis() - start_ms < timeout_ms) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Wi-Fi connected.");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
        drawWifiOkScreen();
        return;
    }

    Serial.println("Wi-Fi connection failed.");
    Serial.print("Wi-Fi status code: ");
    Serial.println(WiFi.status());
    drawWifiFailScreen();
}


// ------------------------------------------------------------
// Async HTTP transport — FreeRTOS queue
//
// Архитектура:
//
//   Ядро 0 — loop() / IMU / кнопки (высокий приоритет)
//     emitProtocolLine(line)
//       → Serial.println(line)          — немедленно
//       → xQueueSend(http_queue, ...)   — кладём в очередь, не ждём HTTP
//
//   Ядро 1 — task_http (низкий приоритет)
//     xQueueReceive(http_queue, ...)
//       → накапливаем батч
//       → HTTP POST когда батч полон или истёк таймер
//
// IMU опрашивается без пауз.
// HTTP POST выполняется параллельно на другом ядре.
//
// Размер очереди HTTP_QUEUE_SIZE:
//   При 100 Hz и POST занимающем 300ms накапливается до 30 строк.
//   Размер 200 даёт запас на случай временных задержек сети.
//   При переполнении строка теряется с предупреждением в Serial.
// ------------------------------------------------------------

static const uint16_t HTTP_QUEUE_SIZE      = 500;  // увеличен: буфер на случай задержек сети
static const uint16_t HTTP_BATCH_MAX_LINES = 20;   // 20 строк = 5 батчей/сек при 100Hz
static const uint32_t HTTP_BATCH_MAX_AGE_MS = 200; // flush по таймеру если батч не заполнился
static const uint32_t HTTP_TIMEOUT_MS      = 2000;

// Очередь строк от IMU-задачи к HTTP-задаче.
// Передаём указатели на String* чтобы не копировать содержимое дважды.
QueueHandle_t http_queue = nullptr;

// Статистика потерь для диагностики.
uint32_t http_queue_dropped = 0;


void http_enqueue(const String& line) {
    if (http_queue == nullptr || !isWifiOk()) {
        return;
    }

    // Создаём копию строки в heap — task_http освободит её.
    String* s = new String(line);

    if (xQueueSend(http_queue, &s, 0) != pdTRUE) {
        // Очередь полна — строка теряется.
        delete s;
        http_queue_dropped++;

        if (http_queue_dropped % 10 == 1) {
            Serial.print("[WARN] HTTP queue full, dropped=");
            Serial.println(http_queue_dropped);
        }
    }
}


// ------------------------------------------------------------
// task_http — HTTP задача на ядре 0
//
// Забирает строки из очереди, накапливает батч,
// отправляет POST когда батч полон или истёк таймер.
//
// Каждый POST использует свежий HTTPClient — надёжнее чем reuse
// при высокой нагрузке и нестабильном Wi-Fi.
// ------------------------------------------------------------

void task_http(void* param) {
    Serial.print("[HTTP] task_http running on core: ");
    Serial.println(xPortGetCoreID());

    String   batch_buffer = "";
    uint16_t batch_count  = 0;

    batch_buffer.reserve(2000);

    auto reset_batch = [&]() {
        batch_buffer = "";
        batch_count  = 0;
    };

    // Отправить произвольный body одним POST.
    auto post_body = [&](const String& body) {
        if (!isWifiOk()) return;

        HTTPClient tmp;
        tmp.begin(LOGGER_URL);
        tmp.addHeader("Content-Type", "text/plain");
        tmp.setTimeout(HTTP_TIMEOUT_MS);
        int code = tmp.POST(body);
        tmp.end();

        if (code != 200) {
            Serial.print("[HTTP] POST failed, code=");
            Serial.println(code);
        }
    };

    auto flush_batch = [&]() {
        if (batch_count == 0) return;
        String body = batch_buffer;
        uint16_t cnt = batch_count;
        reset_batch();
        post_body(body);
    };

    while (true) {
        String* line_ptr = nullptr;

        BaseType_t got = xQueueReceive(
            http_queue,
            &line_ptr,
            pdMS_TO_TICKS(HTTP_BATCH_MAX_AGE_MS)
        );

        if (got == pdTRUE && line_ptr != nullptr) {
            String line = *line_ptr;
            delete line_ptr;

            if (line.startsWith("DATA,")) {
                if (batch_count > 0) batch_buffer += "\n";
                batch_buffer += line;
                batch_count++;

                if (batch_count >= HTTP_BATCH_MAX_LINES) {
                    flush_batch();
                }
            } else {
                // Служебные события: сначала flush DATA, потом само событие
                flush_batch();
                post_body(line);
            }
        } else {
            // Таймаут — flush по возрасту
            flush_batch();
        }
    }
}


// ------------------------------------------------------------
// Запуск HTTP задачи
// ------------------------------------------------------------

void startHttpTask() {
    http_queue = xQueueCreate(HTTP_QUEUE_SIZE, sizeof(String*));

    if (http_queue == nullptr) {
        Serial.println("[ERROR] Failed to create HTTP queue");
        return;
    }

    // Важно: loop() в Arduino ESP32 работает на ядре 1.
    // Поэтому HTTP задачу запускаем на ядре 0 — разные ядра, нет конкуренции.
    BaseType_t result = xTaskCreatePinnedToCore(
        task_http,    // функция задачи
        "http",       // имя задачи
        16384,        // размер стека — HTTPClient + String требуют много места
        nullptr,      // параметры
        1,            // приоритет (1 = низкий)
        nullptr,      // handle (не нужен)
        0             // ядро 0 — loop() на ядре 1, HTTP на ядре 0
    );

    if (result != pdPASS) {
        Serial.println("[ERROR] Failed to start HTTP task");
    } else {
        Serial.println("[HTTP] Async HTTP task started on core 0");
        Serial.print("[HTTP] loop() runs on core: ");
        Serial.println(xPortGetCoreID());
    }
}


// ------------------------------------------------------------
// Единая отправка строки протокола
//
// Serial — немедленно (как раньше).
// HTTP   — через очередь, без блокировки IMU.
// ------------------------------------------------------------

void emitProtocolLine(const String& line) {
    Serial.println(line);
    http_enqueue(line);
}


// ------------------------------------------------------------
// Протокольные события
// ------------------------------------------------------------

void sendDeviceInfoEvent() {
    String line =
        String("EVENT,DEVICE_INFO,") +
        getDeviceMacAddress() + "," +
        String(FIRMWARE_VERSION) + "," +
        String(millis());
    emitProtocolLine(line);
}

void sendSampleRateEvent() {
    String line =
        String("EVENT,SAMPLE_RATE,") +
        String(sample_rate_hz) + "," +
        String(millis());
    emitProtocolLine(line);
}

void sendNewSessionEvent() {
    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    String line =
        String("EVENT,NEW_SESSION,") +
        session_id + "," +
        String(millis());
    emitProtocolLine(line);
}


// ------------------------------------------------------------
// Wi-Fi индикатор для REC экрана
//
// Маленький кружок в правом верхнем углу:
//   зелёный = Wi-Fi есть
//   красный  = Wi-Fi нет
//
// Перерисовываем только кружок, без перерисовки всего экрана.
// ------------------------------------------------------------

void drawWifiIndicator() {
    uint16_t color = isWifiOk() ? MB_GREEN : MB_RED;
    M5.Display.fillCircle(SCREEN_W - 10, 10, 6, color);
}


// ------------------------------------------------------------
// Экран IDLE / READY
// ------------------------------------------------------------

void drawIdleScreen() {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);

    drawVerticalLoggerLabel();

    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    // Wi-Fi status / IP
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(MB_GREY, MB_BLACK);
    M5.Display.drawString(getWifiStatusText(), MAIN_X, 4);
    M5.Display.drawString("RATE " + String(sample_rate_hz) + "Hz", 160, 4);

    // READY
    M5.Display.setTextSize(3);
    M5.Display.setTextColor(MB_GREEN, MB_BLACK);
    M5.Display.drawString("READY", MAIN_X, 22);

    // SESSION
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("SESSION", MAIN_X, 66);

    M5.Display.setTextSize(3);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString(session_id, MAIN_X, 90);

    // Подсказки кнопок
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("A x2 START", MAIN_X, 122);
    M5.Display.drawString("B NEXT", 150, 122);
}


// ------------------------------------------------------------
// Обновление числовых значений на REC-экране
//
// Обновляем только центральную область — меньше мерцания.
// ------------------------------------------------------------

void updateRecordingValues(float acc_norm) {
    M5.Display.setTextDatum(top_left);

    M5.Display.fillRect(MAIN_X, 70, SCREEN_W - MAIN_X, 48, MB_BLACK);

    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("SMP", MAIN_X, 74);
    M5.Display.drawString(String(sample_count), 96, 74);

    M5.Display.drawString("ACC", MAIN_X, 98);
    M5.Display.drawString(String(acc_norm, 2) + " g", 96, 98);

    // Wi-Fi индикатор обновляем вместе с метриками
    drawWifiIndicator();
}


// ------------------------------------------------------------
// Экран записи
// ------------------------------------------------------------

void drawRecordingScreen(float acc_norm) {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);

    drawVerticalLoggerLabel();

    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    // REC + красный кружок
    M5.Display.setTextSize(3);
    M5.Display.setTextColor(MB_RED, MB_BLACK);
    M5.Display.drawString("REC", MAIN_X, 6);
    M5.Display.fillCircle(MAIN_X + 88, 24, 7, MB_RED);

    // Session / record
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    String recordText = String(session_id) + " / R" + String(record_id);
    M5.Display.drawString(recordText, MAIN_X, 44);

    // Метрики + Wi-Fi индикатор
    updateRecordingValues(acc_norm);

    // Подсказка кнопки
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("A STOP", MAIN_X, 122);
}


// ------------------------------------------------------------
// Экран SAVED
//
// Показывается на 1.2 секунды после остановки записи.
// Даёт пользователю понять, что запись завершена и сохранена.
// ------------------------------------------------------------

void showSavedScreen(uint32_t saved_record_id, uint32_t saved_sample_count) {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);

    drawVerticalLoggerLabel();

    M5.Display.setTextColor(MB_GREEN, MB_BLACK);
    M5.Display.setTextSize(3);
    M5.Display.drawString("SAVED", MAIN_X, 16);

    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("R" + String(saved_record_id), MAIN_X, 60);

    M5.Display.setTextColor(MB_GREY, MB_BLACK);
    M5.Display.drawString(String(saved_sample_count) + " smp", MAIN_X, 86);

    delay(SAVED_SCREEN_MS);
}


// ------------------------------------------------------------
// Запуск записи
// ------------------------------------------------------------

void startRecord() {
    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    is_recording   = true;
    sample_id      = 0;
    sample_count   = 0;
    last_acc_norm  = 0.0f;
    last_sample_ms = millis();

    String line =
        String("EVENT,START,") +
        session_id + "," +
        String(record_id) + "," +
        String(millis());

    emitProtocolLine(line);
    drawRecordingScreen(last_acc_norm);
}


// ------------------------------------------------------------
// Остановка записи
// ------------------------------------------------------------

void stopRecord() {
    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    String line =
        String("EVENT,STOP,") +
        session_id + "," +
        String(record_id) + "," +
        String(millis()) + "," +
        String(sample_count);

    emitProtocolLine(line);

    is_recording = false;

    // Сохраняем для экрана SAVED перед инкрементом record_id
    last_record_sample_count = sample_count;
    uint32_t finished_record_id = record_id;

    record_id++;

    // Показываем подтверждение перед возвратом на READY
    showSavedScreen(finished_record_id, last_record_sample_count);

    drawIdleScreen();
}


// ------------------------------------------------------------
// Переход к следующей сессии
// ------------------------------------------------------------

void nextSession() {
    if (is_recording) {
        return;
    }

    session_number++;
    record_id    = 1;
    sample_id    = 0;
    sample_count = 0;
    last_acc_norm = 0.0f;
    waiting_for_second_click = false;

    sendNewSessionEvent();
    drawIdleScreen();
}


// ------------------------------------------------------------
// Обработка Button A
//
// Во время записи:  одиночный клик = STOP
// В IDLE:           двойной клик   = START
// ------------------------------------------------------------

void handleButtonA() {
    if (!M5.BtnA.wasClicked()) {
        return;
    }

    uint32_t now = millis();

    if (is_recording) {
        stopRecord();
        waiting_for_second_click = false;
        return;
    }

    if (!waiting_for_second_click) {
        waiting_for_second_click = true;
        last_click_ms = now;
        return;
    }

    if (now - last_click_ms <= DOUBLE_CLICK_WINDOW_MS) {
        waiting_for_second_click = false;
        startRecord();
        return;
    }

    // Второй клик пришёл слишком поздно — считаем его новым первым.
    last_click_ms = now;
}


// ------------------------------------------------------------
// Обработка Button B
// ------------------------------------------------------------

void handleButtonB() {
    if (M5.BtnB.wasClicked()) {
        nextSession();
    }
}


// ------------------------------------------------------------
// Сброс ожидания второго клика
// ------------------------------------------------------------

void handleClickTimeout() {
    if (!waiting_for_second_click) {
        return;
    }

    if (millis() - last_click_ms > DOUBLE_CLICK_WINDOW_MS) {
        waiting_for_second_click = false;
    }
}


// ------------------------------------------------------------
// Чтение IMU и отправка строки DATA
//
// Используем статический буфер data_line_buf вместо String
// для снижения heap fragmentation при 100 Hz.
// ------------------------------------------------------------

void sendImuSample() {
    uint32_t now = millis();

    if (now - last_sample_ms < sample_interval_ms) {
        return;
    }

    last_sample_ms = now;

    bool imu_updated = M5.Imu.update();

    if (!imu_updated) {
        char session_id[8];
        getSessionId(session_id, sizeof(session_id));

        snprintf(data_line_buf, sizeof(data_line_buf),
            "EVENT,IMU_NOT_UPDATED,%s,%lu,%lu",
            session_id, record_id, now);

        emitProtocolLine(String(data_line_buf));
        return;
    }

    auto data = M5.Imu.getImuData();

    float ax = data.accel.x;
    float ay = data.accel.y;
    float az = data.accel.z;
    float gx = data.gyro.x;
    float gy = data.gyro.y;
    float gz = data.gyro.z;

    float acc_norm = sqrt(ax * ax + ay * ay + az * az);
    last_acc_norm  = acc_norm;

    sample_id++;
    sample_count++;

    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    snprintf(data_line_buf, sizeof(data_line_buf),
        "DATA,%s,%lu,%lu,%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f",
        session_id, record_id, sample_id, now,
        ax, ay, az, gx, gy, gz, acc_norm);

    emitProtocolLine(String(data_line_buf));

    // Экран обновляем по времени (~5 раз в секунду), не по счётчику сэмплов.
    // Это даёт предсказуемое поведение на любой частоте дискретизации.
    static uint32_t last_screen_update_ms = 0;

    if (sample_count == 1 || now - last_screen_update_ms >= 200) {
        last_screen_update_ms = now;
        updateRecordingValues(acc_norm);
    }
}


// ------------------------------------------------------------
// setup()
// ------------------------------------------------------------

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);

    M5.Display.setRotation(1);
    M5.Display.setBrightness(80);
    M5.Display.setTextFont(1);
    M5.Display.setTextDatum(top_left);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.fillScreen(MB_BLACK);

    showSplashScreen();

    Serial.begin(115200);
    delay(500);

    Serial.println("MotionBlocks IMU logger v0.8.0");
    Serial.println("Protocol:");
    Serial.println("EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms");
    Serial.println("EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms");
    Serial.println("EVENT,NEW_SESSION,session_id,timestamp_ms");
    Serial.println("EVENT,START,session_id,record_id,timestamp_ms");
    Serial.println("DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm");
    Serial.println("EVENT,STOP,session_id,record_id,timestamp_ms,sample_count");
    Serial.println();
    Serial.print("HTTP logger URL: ");
    Serial.println(LOGGER_URL);

    selectSampleRateAtStartup();
    connectToWifi();

    // Запускаем HTTP задачу на ядре 0.
    // loop() работает на ядре 1 — разные ядра, нет конкуренции за CPU.
    startHttpTask();

    sendDeviceInfoEvent();
    sendSampleRateEvent();

    // Пауза между SAMPLE_RATE и NEW_SESSION.
    //
    // Причина: оба события уходят в HTTP очередь асинхронно.
    // Logger должен обработать SAMPLE_RATE и обновить sample_rate_hz
    // ДО того как откроет CSV файл по событию NEW_SESSION.
    // Без паузы NEW_SESSION может прийти раньше и файл получит
    // имя с дефолтным значением 10Hz вместо реально выбранного.
    //
    // 500ms достаточно для одного HTTP POST round-trip.
    delay(500);

    sendNewSessionEvent();

    drawIdleScreen();
}


// ------------------------------------------------------------
// loop()
// ------------------------------------------------------------

void loop() {
    M5.update();

    handleButtonA();
    handleButtonB();
    handleClickTimeout();

    if (is_recording) {
        sendImuSample();
    }
}
