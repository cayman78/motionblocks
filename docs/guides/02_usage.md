# Руководство по использованию — MotionBlocks

Этот документ описывает полный цикл работы с системой: от запуска регистрации до просмотра и анализа данных.

Перед использованием убедись что окружение настроено согласно `01_setup.md`.

---

## Обзор системы

```
M5StickC Plus2
  → Wi-Fi
  → http_logger.py         (приём данных, запись CSV)
  → data/raw/              (сырые данные)
  → motion_browser.py      (просмотр и редактирование метаданных)
  → analyze_recordings.py  (анализ качества и графики)
  → compute_features.py    (извлечение фич, скользящее окно)
  → data/analysis/         (результаты анализа и фичи)
  → Orange Data Mining     (обучение классификатора)
```

---

## 1. Подготовка перед записью

### 1.1 Узнай IP-адрес ноутбука

```powershell
ipconfig
```

Найди **IPv4-адрес** для Wi-Fi адаптера, например `192.168.1.100`.

### 1.2 Обнови LOGGER_URL в прошивке

Открой `firmware/m5stickc-plus2/src/wifi_config.h` и убедись что адрес актуален:

```cpp
#define LOGGER_URL "http://192.168.1.100:8080/line"
```

Если IP изменился — обнови файл и перепрошей устройство:

```powershell
pio run --target upload --upload-port COM6
```

---

## 2. Запуск регистрации

### 2.1 Активируй виртуальное окружение

```powershell
cd C:\путь\к\motionblocks
.\.venv\Scripts\Activate.ps1
```

### 2.2 Запусти HTTP logger

```powershell
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5-01 --create-metadata
```

Параметры:

| Параметр | Описание |
|---|---|
| `--experiment-id` | Идентификатор эксперимента, например `EXP01` |
| `--device-id` | Идентификатор устройства из `devices.json`, например `m5-01` |
| `--create-metadata` | Автоматически создать черновые записи метаданных |

Logger запустится и будет ждать подключения устройства:

```
[HTTP] Logger started on 0.0.0.0:8080
[HTTP] Waiting for device...
```

### 2.3 Включи устройство

Нажми кнопку питания на M5StickC Plus2. Устройство пройдёт через несколько экранов:

**Экран выбора частоты дискретизации:**

```
SAMPLE RATE
5 / 10 / 25 / 50 / 100 Hz
A NEXT    B OK
```

Кнопка A переключает частоту по кругу. Кнопка B подтверждает выбор. Если не нажимать кнопки — через 5 секунд автоматически выберется 10 Hz.

**Экран подключения к Wi-Fi** — устройство подключается к сети.

**Экран READY:**

```
WiFi 192.168.1.57
READY
SESSION A001
RATE 100Hz
A x2 START    B NEXT
```

Когда устройство появится на READY экране, logger выведет:

```
EVENT,DEVICE_INFO,...
EVENT,SAMPLE_RATE,100,...
EVENT,NEW_SESSION,A001,...
[CONFIG] sample_rate_hz=100
[SESSION] A001
[FILE] data\raw\EXP01\m5-01\run_A_session_A001_100Hz.csv
```

### 2.4 Управление записью

| Действие | Кнопка |
|---|---|
| Начать запись | Двойной клик по кнопке A |
| Остановить запись | Одиночный клик по кнопке A |
| Следующая сессия | Кнопка B |

Во время записи экран показывает текущие метрики:

```
REC  ●
A001 / R1
SMP  247
ACC  1.02 g
A STOP
```

После остановки кратко появится экран **SAVED**, затем устройство вернётся на READY.

Logger в консоли будет периодически печатать прогресс и итог каждой записи:

```
[REC] A001/R1 — 201 samples
[REC] A001/R1 — 401 samples
[STOP] session=A001, record=1, samples=497, duration=5.1s, file=run_A_session_A001_100Hz.csv
```

### 2.5 Завершение сессии

Когда все нужные записи сделаны — останови logger нажатием `Ctrl+C` в терминале.

Данные уже сохранены в `data/raw/`.

---

## 3. Структура файлов данных

После записи файлы появятся в следующих местах:

```
data/
├── raw/
│   └── EXP01/
│       └── m5-01/
│           └── run_A_session_A001_100Hz.csv   ← сырые данные
│
├── metadata/
│   ├── experiments.json        ← описание экспериментов
│   ├── recording_sessions.json ← описание сессий
│   ├── devices.json            ← реестр устройств
│   └── feature_config.json     ← параметры окна для compute_features
│
└── analysis/
    └── EXP01/
        ├── session_quality.csv     ← метрики качества
        ├── plots/                  ← графики acc_norm и dt_ms
        └── features/
            └── features.csv        ← фичи для ML
```

**Имя файла** кодирует всю необходимую идентификацию:

```
run_A_session_A001_100Hz.csv
     ↑           ↑      ↑
     run ID    сессия  частота
```

`run_A` — идентификатор запуска, назначается logger'ом. При каждом новом запуске logger'а буква увеличивается (A → B → C). Это предотвращает перезапись файлов при повторном включении устройства с той же сессией A001.

---

## 4. Просмотр данных — Motion Browser

Motion Browser — локальный веб-интерфейс для просмотра записей и редактирования метаданных.

Запусти в отдельном терминале (с активированным окружением):

```powershell
streamlit run tools/motion_browser.py
```

Браузер автоматически откроется на `http://localhost:8501`.

В левой панели выбери режим работы:

- **🗂 Обзор** — список экспериментов и сессий с фильтрами
- **📈 Просмотр** — графики acc_norm, осей акселерометра и гироскопа, dt_ms
- **✏️ Редактор** — заполнение метаданных: тип движения, субъект, статус, комментарии

### Заполнение метаданных

После записи метаданные создаются автоматически со статусом `draft`. Рекомендуется сразу заполнить:

- `movement_type` — тип движения (walking, jumping, idle, shaking и др.)
- `movement_label` — более конкретное описание (walking_normal, jumps_basic)
- `subject_id` — кто выполнял движение (adult_01, child_01)
- `status` — изменить с `draft` на `raw` после проверки

---

## 5. Анализ качества записей

`analyze_recordings.py` рассчитывает метрики качества и сохраняет графики.

### Анализ одного файла

```powershell
python tools/analyze_recordings.py --file data\raw\EXP01\m5-01\run_A_session_A001_100Hz.csv
```

### Анализ всего эксперимента

```powershell
python tools/analyze_recordings.py --experiment EXP01
```

### Анализ всех экспериментов

```powershell
python tools/analyze_recordings.py --all
```

Вывод в консоль показывает метрики по каждому файлу:

```
✅ OK                    run_A_session_A001_100Hz.csv
  DATA строк:       1142
  Длительность:     14.5 s
  Частота (config): 100 Hz
  Частота (факт):   100.0 Hz
  dt_ms mean/med:   10.0 / 10.0 ms
  Gaps:             0
```

Возможные статусы качества:

| Статус | Описание |
|---|---|
| ✅ OK | Запись пригодна для использования |
| ⚠️ WARN_GAPS | Обнаружены временные пропуски в данных |
| ⚠️ WARN_SHORT | Запись слишком короткая |
| ⚠️ WARN_RATE_MISMATCH | Фактическая частота значительно отличается от настроенной |
| ❌ BAD_EMPTY | Файл не содержит данных |

---

## 6. Результаты анализа

Все результаты сохраняются в `data/analysis/`:

```
data/
└── analysis/
    └── EXP01/
        ├── session_quality.csv        ← таблица метрик по всем файлам
        └── plots/
            ├── run_A_session_A001_100Hz_acc_norm.png
            ├── run_A_session_A001_100Hz_dt_ms.png
            └── ...
```

`session_quality.csv` удобно открывать в Excel или pandas для сравнения нескольких сессий.

Графики `acc_norm` показывают форму сигнала по записям — полезны для проверки что движение записалось правильно.

Графики `dt_ms` показывают равномерность временных интервалов между сэмплами — горизонтальная линия на уровне ожидаемого интервала означает чистые данные без пропусков.

---

## 7. Извлечение фич для ML

После того как данные проверены (`analyze_recordings.py` показал `✅ OK`) и метаданные заполнены (`movement_type` в motion_browser.py), можно извлечь фичи для обучения модели.

### 7.1 Заполни movement_type

Перед запуском убедись что в motion_browser.py у каждой сессии заполнен `movement_type`. Скрипт пропускает сессии со значением `unknown`.

### 7.2 Запусти compute_features.py

```powershell
python tools/compute_features.py --experiment EXP01
```

Скрипт нарежет каждую запись скользящим окном и посчитает фичи:

```
Параметры: окно=2.0s  шаг=0.5s  обрезка=1.0s+1.0s

Эксперимент: EXP01  (9 сессий)
  EXP01_m5-01_A_A001  [walking]  → 47 окон
  EXP01_m5-01_A_A002  [running]  → 31 окно
  ...

  Всего окон: 570
  По классам:
    walking: 252
    running:  99
    ...

  Сохранено: data\analysis\features\EXP01\features.csv
```

### 7.3 Параметры окна

Параметры по умолчанию хранятся в `data/metadata/feature_config.json`. Любой параметр можно переопределить через CLI:

```powershell
# Изменить размер и шаг окна
python tools/compute_features.py --experiment EXP01 --window-sec 1.0 --step-sec 0.25

# Изменить уровень покоя для zero-crossing
python tools/compute_features.py --experiment EXP01 --acc-norm-rest 1.05
```

---

## 8. Обучение классификатора в Orange Data Mining

### 8.1 Открыть данные

- Запусти Orange
- Создай новый проект: **New**
- Перетащи виджет **File** (раздел Data) на canvas
- Двойной клик → выбери `data/analysis/features/EXP01/features.csv`

### 8.2 Настроить роли колонок

В виджете File в колонке **Role**:

| Колонки | Role |
|---|---|
| `movement_type` | **target** |
| `experiment_id`, `device_id`, `session_uid`, `recording_run_id`, `device_session_id`, `record_id`, `window_idx`, `window_start_ms`, `window_end_ms`, `sample_count`, `sample_rate_hz`, `movement_label`, `subject_id` | **meta** |
| Все числовые фичи (`acc_norm_mean` и далее) | **feature** (оставить как есть) |

Нажми **Apply**.

### 8.3 Собрать pipeline для обучения

Перетащи на canvas:

- **Random Forest** (раздел Model)
- **Test and Score** (раздел Evaluate)

Соедини:

```
File → Random Forest → Test and Score
File → Test and Score
```

Двойной клик на **Test and Score** → метод **Cross Validation**, folds: **5** → смотри колонку **CA** (Classification Accuracy).

### 8.4 Confusion Matrix

Добавь виджет **Confusion Matrix** (раздел Evaluate):

```
Test and Score → Confusion Matrix
```

Двойной клик → матрица показывает где модель ошибается по классам.

### 8.5 Предсказание на новых данных

Для предсказания на записях без разметки (новый субъект или новая сессия):

1. Запусти `compute_features.py` для нового эксперимента (EXP15)
2. Добавь второй виджет **File** → загрузи `features/EXP15/features.csv`
3. В этом File: `movement_type` → **meta** (не target)
4. Добавь виджет **Predictions** (раздел Evaluate)
5. Соедини:

```
Random Forest  → Predictions
File (EXP15)   → Predictions
```

Двойной клик на **Predictions** → таблица с предсказанным `movement_type` для каждого окна.

Колонка `time_from_record_start_sec` показывает в какой момент записи находится каждое окно.

---

## Типичный рабочий сеанс

```powershell
# 1. Открыть терминал, активировать окружение
cd C:\путь\к\motionblocks
.\.venv\Scripts\Activate.ps1

# 2. Запустить logger (в первом терминале)
python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5-01 --create-metadata

# 3. Включить устройство, выбрать частоту, делать записи
# ...после окончания нажать Ctrl+C в logger

# 4. Открыть второй терминал, активировать окружение
.\.venv\Scripts\Activate.ps1

# 5. Запустить браузер — заполнить movement_type для каждой сессии
streamlit run tools/motion_browser.py

# 6. Проверить качество данных
python tools/analyze_recordings.py --experiment EXP01

# 7. Извлечь фичи для ML
python tools/compute_features.py --experiment EXP01

# 8. Открыть Orange Data Mining → загрузить features.csv → обучить модель
```
