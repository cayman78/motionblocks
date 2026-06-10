#include <M5Unified.h>
#include <math.h>

// ============================================================
// MotionBlocks — IMU logger v0.3
//
// Новое в v0.3:
// - добавлен session_id;
// - Button B переключает на следующую сессию;
// - Button A double click запускает запись;
// - Button A single click во время записи останавливает запись;
// - experiment_id, device_id, subject_id прошивка НЕ знает.
//
// Serial-протокол:
//
// EVENT,NEW_SESSION,session_id,timestamp_ms
// EVENT,START,session_id,record_id,timestamp_ms
// DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
// EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
// ============================================================


// ------------------------------------------------------------
// Настройки
// ------------------------------------------------------------

// Частота записи: 10 Гц = один сэмпл каждые 100 мс.
static const uint32_t SAMPLE_INTERVAL_MS = 100;

// Максимальный интервал между двумя кликами Button A,
// чтобы считать их двойным нажатием.
static const uint32_t DOUBLE_CLICK_WINDOW_MS = 400;


// ------------------------------------------------------------
// Цвета
// ------------------------------------------------------------
//
// Некоторые цвета уже могут быть определены в M5Unified,
// но свои имена безопаснее и понятнее для layout-кода.
// ------------------------------------------------------------
static const uint16_t MB_BLACK = BLACK;
static const uint16_t MB_WHITE = WHITE;
static const uint16_t MB_GREEN = GREEN;
static const uint16_t MB_RED = RED;
static const uint16_t MB_GREY = 0xC618;
static const uint16_t MB_DARKGREY = 0x7BEF;


// ------------------------------------------------------------
// Координаты layout
// ------------------------------------------------------------
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

// Номер текущей сессии.
// На экране и в Serial будет отображаться как A001, A002, A003...
uint32_t session_number = 1;

// Номер текущей попытки внутри сессии.
uint32_t record_id = 1;

// Номер сэмпла внутри текущей попытки.
uint32_t sample_id = 0;

// Количество сэмплов внутри текущей попытки.
uint32_t sample_count = 0;

// Идёт ли сейчас запись.
bool is_recording = false;

// Время последнего сэмпла.
uint32_t last_sample_ms = 0;

// Последнее значение нормы ускорения.
// Нужно только для отображения на экране.
float last_acc_norm = 0.0f;


// ------------------------------------------------------------
// Состояние кнопок
// ------------------------------------------------------------

// Время первого клика Button A.
uint32_t last_click_ms = 0;

// Ждём ли второй клик Button A для double click.
bool waiting_for_second_click = false;


// ------------------------------------------------------------
// Формирование session_id
//
// session_number = 1  -> A001
// session_number = 2  -> A002
// session_number = 15 -> A015
// ------------------------------------------------------------
void getSessionId(char* buffer, size_t buffer_size) {
    snprintf(buffer, buffer_size, "A%03lu", session_number);
}


// ------------------------------------------------------------
// Отправка события NEW_SESSION
// ------------------------------------------------------------
void sendNewSessionEvent() {
    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    Serial.print("EVENT,NEW_SESSION,");
    Serial.print(session_id);
    Serial.print(",");
    Serial.println(millis());
}


// ------------------------------------------------------------
// Экран: вертикальная надпись LOGGER
//
// Важно:
// Не вращаем текст через setRotation.
// Просто рисуем буквы столбиком — это устойчивее.
// ------------------------------------------------------------
void drawVerticalLoggerLabel() {
    M5.Display.setTextDatum(top_left);
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_GREY, MB_BLACK);

    int x = RAIL_X;
    int y = 8;
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
// Экран IDLE / READY
// ------------------------------------------------------------
void drawIdleScreen() {
    M5.Display.fillScreen(MB_BLACK);
    M5.Display.setTextDatum(top_left);

    drawVerticalLoggerLabel();

    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    // Главный статус
    M5.Display.setTextSize(3);
    M5.Display.setTextColor(MB_GREEN, MB_BLACK);
    M5.Display.drawString("READY", MAIN_X, 12);

    // Сессия
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("SESSION", MAIN_X, 58);

    M5.Display.setTextSize(3);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString(session_id, MAIN_X, 84);

    // Подсказки по кнопкам
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("A x2 START", MAIN_X, 122);
    M5.Display.drawString("B NEXT", 150, 122);
}


// ------------------------------------------------------------
// Обновление числовых значений на REC-экране
//
// Обновляем только центральную область, не весь экран.
// Так меньше мерцания и нет наложения старого текста.
// ------------------------------------------------------------
void updateRecordingValues(float acc_norm) {
    M5.Display.setTextDatum(top_left);

    // Чистим только область с метриками.
    M5.Display.fillRect(MAIN_X, 70, 200, 48, MB_BLACK);

    // Строка SAMPLES
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("SMP", MAIN_X, 74);
    M5.Display.drawString(String(sample_count), 96, 74);

    // Строка ACC
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("ACC", MAIN_X, 98);
    M5.Display.drawString(String(acc_norm, 2) + " g", 96, 98);
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

    // REC status
    M5.Display.setTextSize(3);
    M5.Display.setTextColor(MB_RED, MB_BLACK);
    M5.Display.drawString("REC", MAIN_X, 6);
    M5.Display.fillCircle(MAIN_X + 88, 24, 7, MB_RED);

    // Session / record
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);

    String recordText = String(session_id) + " / R" + String(record_id);
    M5.Display.drawString(recordText, MAIN_X, 44);

    // Метрики
    updateRecordingValues(acc_norm);

    // Подсказка по кнопке
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.drawString("A STOP", MAIN_X, 122);
}


// ------------------------------------------------------------
// Запуск записи
// ------------------------------------------------------------
void startRecord() {
    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    is_recording = true;
    sample_id = 0;
    sample_count = 0;
    last_acc_norm = 0.0f;
    last_sample_ms = millis();

    Serial.print("EVENT,START,");
    Serial.print(session_id);
    Serial.print(",");
    Serial.print(record_id);
    Serial.print(",");
    Serial.println(millis());

    drawRecordingScreen(last_acc_norm);
}


// ------------------------------------------------------------
// Остановка записи
// ------------------------------------------------------------
void stopRecord() {
    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    Serial.print("EVENT,STOP,");
    Serial.print(session_id);
    Serial.print(",");
    Serial.print(record_id);
    Serial.print(",");
    Serial.print(millis());
    Serial.print(",");
    Serial.println(sample_count);

    is_recording = false;

    // Следующая попытка внутри этой же сессии.
    record_id++;

    drawIdleScreen();
}


// ------------------------------------------------------------
// Переход к следующей сессии
//
// Важно:
// - если запись идёт, Button B игнорируется;
// - при переходе к новой сессии record_id снова начинается с 1;
// - прошивка не знает, в какой experiment попадёт сессия.
// ------------------------------------------------------------
void nextSession() {
    if (is_recording) {
        return;
    }

    session_number++;
    record_id = 1;
    sample_id = 0;
    sample_count = 0;
    last_acc_norm = 0.0f;
    waiting_for_second_click = false;

    sendNewSessionEvent();
    drawIdleScreen();
}


// ------------------------------------------------------------
// Обработка Button A
//
// Если запись идёт:
//   одиночный клик A = stop
//
// Если запись не идёт:
//   двойной клик A = start
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

    // Если второй клик пришёл слишком поздно,
    // считаем его новым первым кликом.
    last_click_ms = now;
}


// ------------------------------------------------------------
// Обработка Button B
//
// Button B = перейти к следующей сессии.
// ------------------------------------------------------------
void handleButtonB() {
    if (M5.BtnB.wasClicked()) {
        nextSession();
    }
}


// ------------------------------------------------------------
// Сброс ожидания второго клика Button A
// ------------------------------------------------------------
void handleClickTimeout() {
    if (!waiting_for_second_click) {
        return;
    }

    uint32_t now = millis();

    if (now - last_click_ms > DOUBLE_CLICK_WINDOW_MS) {
        waiting_for_second_click = false;
    }
}


// ------------------------------------------------------------
// Чтение IMU и отправка строки DATA
// ------------------------------------------------------------
void sendImuSample() {
    uint32_t now = millis();

    if (now - last_sample_ms < SAMPLE_INTERVAL_MS) {
        return;
    }

    last_sample_ms = now;

    bool imu_updated = M5.Imu.update();

    if (!imu_updated) {
        char session_id[8];
        getSessionId(session_id, sizeof(session_id));

        Serial.print("EVENT,IMU_NOT_UPDATED,");
        Serial.print(session_id);
        Serial.print(",");
        Serial.print(record_id);
        Serial.print(",");
        Serial.println(now);
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
    last_acc_norm = acc_norm;

    sample_id++;
    sample_count++;

    char session_id[8];
    getSessionId(session_id, sizeof(session_id));

    Serial.print("DATA,");
    Serial.print(session_id);
    Serial.print(",");
    Serial.print(record_id);
    Serial.print(",");
    Serial.print(sample_id);
    Serial.print(",");
    Serial.print(now);
    Serial.print(",");
    Serial.print(ax, 4);
    Serial.print(",");
    Serial.print(ay, 4);
    Serial.print(",");
    Serial.print(az, 4);
    Serial.print(",");
    Serial.print(gx, 4);
    Serial.print(",");
    Serial.print(gy, 4);
    Serial.print(",");
    Serial.print(gz, 4);
    Serial.print(",");
    Serial.println(acc_norm, 4);

    // Экран обновляем не на каждом сэмпле, а примерно 2 раза в секунду.
    // При sample_count == 1 обновляем сразу, чтобы не висел ноль.
    if (sample_count == 1 || sample_count % 5 == 0) {
        updateRecordingValues(acc_norm);
    }
}


// ------------------------------------------------------------
// setup()
// ------------------------------------------------------------
void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);

    // Фиксируем landscape-ориентацию.
    // Если экран окажется вверх ногами — заменить 1 на 3.
    M5.Display.setRotation(1);

    M5.Display.setBrightness(80);
    M5.Display.setTextFont(1);
    M5.Display.setTextDatum(top_left);
    M5.Display.setTextColor(MB_WHITE, MB_BLACK);
    M5.Display.fillScreen(MB_BLACK);

    showSplashScreen();

    Serial.begin(115200);
    delay(500);

    Serial.println("MotionBlocks IMU logger v0.3");
    Serial.println("Protocol:");
    Serial.println("EVENT,NEW_SESSION,session_id,timestamp_ms");
    Serial.println("EVENT,START,session_id,record_id,timestamp_ms");
    Serial.println("DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm");
    Serial.println("EVENT,STOP,session_id,record_id,timestamp_ms,sample_count");

    // Сообщаем компьютеру стартовую сессию A001.
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
