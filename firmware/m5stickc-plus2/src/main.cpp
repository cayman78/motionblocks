#include <M5Unified.h>
#include <math.h>

// ============================================================
// MotionBlocks — IMU logger v0.2
//
// Функциональность:
// - устройство находится в режиме ожидания;
// - двойное нажатие Button A запускает запись;
// - одиночное нажатие Button A во время записи останавливает запись;
// - во время записи IMU-данные отправляются в Serial в CSV-подобном формате;
// - на экране отображается состояние устройства и номер записи.
//
// Serial-протокол:
//
// EVENT,START,record_id,timestamp_ms
// DATA,record_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
// EVENT,STOP,record_id,timestamp_ms,sample_count
// ============================================================


// ------------------------------------------------------------
// Настройки частоты опроса
// ------------------------------------------------------------

// Интервал между измерениями IMU.
// 100 мс = 10 Гц.
// Для первого прототипа 10 Гц достаточно.
static const uint32_t SAMPLE_INTERVAL_MS = 100;

// Максимальное время между двумя кликами,
// чтобы считать их двойным нажатием.
static const uint32_t DOUBLE_CLICK_WINDOW_MS = 400;


// ------------------------------------------------------------
// Глобальные переменные состояния
// ------------------------------------------------------------

// Время последнего измерения IMU.
uint32_t last_sample_ms = 0;

// Идёт ли сейчас запись.
bool is_recording = false;

// Номер текущей / следующей записи.
// Пока хранится только в оперативной памяти.
// После перезагрузки снова начнётся с 1.
uint32_t record_id = 1;

// Количество сэмплов внутри текущей записи.
uint32_t sample_count = 0;

// Время последнего одиночного клика.
// Используется для определения двойного клика.
uint32_t last_click_ms = 0;

// Флаг: был первый клик, ждём второй клик.
bool waiting_for_second_click = false;


// ------------------------------------------------------------
// Отрисовка экрана в режиме ожидания
// ------------------------------------------------------------
void drawIdleScreen() {
    M5.Display.fillScreen(BLACK);
    M5.Display.setRotation(1);

    M5.Display.setTextSize(2);
    M5.Display.setCursor(5, 5);
    M5.Display.println("MotionBlocks");

    M5.Display.setTextSize(1);
    M5.Display.println("IMU logger v0.2");

    M5.Display.setCursor(5, 45);
    M5.Display.println("Status: IDLE");

    M5.Display.setCursor(5, 65);
    M5.Display.printf("Next record: #%lu\n", record_id);

    M5.Display.setCursor(5, 95);
    M5.Display.println("Double click A");
    M5.Display.println("to start");
}


// ------------------------------------------------------------
// Отрисовка экрана во время записи
// ------------------------------------------------------------
void drawRecordingScreen() {
    M5.Display.fillScreen(BLACK);
    M5.Display.setRotation(1);

    M5.Display.setTextSize(2);
    M5.Display.setCursor(5, 5);
    M5.Display.println("MotionBlocks");

    M5.Display.setTextSize(1);
    M5.Display.println("Recording");

    M5.Display.setCursor(5, 45);
    M5.Display.printf("REC #%lu\n", record_id);

    M5.Display.setCursor(5, 65);
    M5.Display.printf("samples: %lu\n", sample_count);

    M5.Display.setCursor(5, 95);
    M5.Display.println("Click A to stop");
}


// ------------------------------------------------------------
// Запуск новой записи
// ------------------------------------------------------------
void startRecord() {
    is_recording = true;
    sample_count = 0;
    last_sample_ms = millis();

    // Сообщаем компьютеру, что началась новая запись.
    Serial.print("EVENT,START,");
    Serial.print(record_id);
    Serial.print(",");
    Serial.println(millis());

    drawRecordingScreen();
}


// ------------------------------------------------------------
// Остановка текущей записи
// ------------------------------------------------------------
void stopRecord() {
    // Сообщаем компьютеру, что запись завершена.
    // Передаём номер записи, время остановки и число сэмплов.
    Serial.print("EVENT,STOP,");
    Serial.print(record_id);
    Serial.print(",");
    Serial.print(millis());
    Serial.print(",");
    Serial.println(sample_count);

    is_recording = false;

    // Следующая запись получит следующий номер.
    record_id++;

    drawIdleScreen();
}


// ------------------------------------------------------------
// Обработка кнопки Button A
//
// Логика:
// - если запись идёт, одиночный клик останавливает запись;
// - если запись не идёт, двойной клик запускает запись.
// ------------------------------------------------------------
void handleButton() {
    // Проверяем, был ли короткий клик по Button A.
    if (!M5.BtnA.wasClicked()) {
        return;
    }

    uint32_t now = millis();

    // Если запись уже идёт — любой клик останавливает запись.
    if (is_recording) {
        stopRecord();
        waiting_for_second_click = false;
        return;
    }

    // Если записи нет и это первый клик —
    // запоминаем время и ждём второй клик.
    if (!waiting_for_second_click) {
        waiting_for_second_click = true;
        last_click_ms = now;
        return;
    }

    // Если второй клик пришёл достаточно быстро —
    // считаем это двойным нажатием и запускаем запись.
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
// Сброс ожидания второго клика
//
// Если второй клик не пришёл в течение DOUBLE_CLICK_WINDOW_MS,
// возвращаемся в обычное состояние.
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
// Чтение IMU и отправка одного сэмпла в Serial
// ------------------------------------------------------------
void sendImuSample() {
    uint32_t now = millis();

    // Проверяем, пора ли брать следующий сэмпл.
    if (now - last_sample_ms < SAMPLE_INTERVAL_MS) {
        return;
    }

    last_sample_ms = now;

    // Важно:
    // M5.Imu.update() обновляет внутренние данные датчика.
    // Без этого getImuData() может возвращать старые значения.
    bool imu_updated = M5.Imu.update();

    if (!imu_updated) {
        Serial.print("EVENT,IMU_NOT_UPDATED,");
        Serial.print(record_id);
        Serial.print(",");
        Serial.println(now);
        return;
    }

    // Получаем данные акселерометра и гироскопа.
    auto data = M5.Imu.getImuData();

    float ax = data.accel.x;
    float ay = data.accel.y;
    float az = data.accel.z;

    float gx = data.gyro.x;
    float gy = data.gyro.y;
    float gz = data.gyro.z;

    // Норма ускорения.
    // В покое должна быть примерно около 1g,
    // потому что акселерометр видит ускорение свободного падения.
    float acc_norm = sqrt(ax * ax + ay * ay + az * az);

    sample_count++;

    // Отправляем строку данных.
    Serial.print("DATA,");
    Serial.print(record_id);
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

    // Чтобы экран не мерцал слишком часто,
    // обновляем количество сэмплов не на каждом измерении,
    // а примерно раз в 5 сэмплов.
    if (sample_count % 10 == 0) {
        M5.Display.fillRect(0, 65, 240, 35, BLACK);
        M5.Display.setCursor(5, 65);
        M5.Display.printf("samples: %lu\n", sample_count);
        M5.Display.printf("acc: %.2f g\n", acc_norm);
    }
}


// ------------------------------------------------------------
// setup() выполняется один раз при старте устройства
// ------------------------------------------------------------
void setup() {
    // Инициализация M5StickC Plus2.
    auto cfg = M5.config();
    M5.begin(cfg);

    // Инициализация Serial.
    Serial.begin(115200);
    delay(500);

    // Печатаем справочную информацию в Serial.
    Serial.println("MotionBlocks IMU logger v0.2");
    Serial.println("Protocol:");
    Serial.println("EVENT,START,record_id,timestamp_ms");
    Serial.println("DATA,record_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm");
    Serial.println("EVENT,STOP,record_id,timestamp_ms,sample_count");

    // Стартуем в режиме ожидания.
    drawIdleScreen();
}


// ------------------------------------------------------------
// loop() выполняется постоянно
// ------------------------------------------------------------
void loop() {
    // Обновляем внутреннее состояние M5:
    // кнопки, питание и прочие системные вещи.
    M5.update();

    // Обрабатываем нажатия кнопки.
    handleButton();

    // Проверяем, не истекло ли окно ожидания второго клика.
    handleClickTimeout();

    // Если запись идёт — читаем IMU и отправляем данные.
    // Если запись не идёт — данные не отправляются.
    if (is_recording) {
        sendImuSample();
    }
}
