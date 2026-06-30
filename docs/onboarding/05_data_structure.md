# Структура данных — MotionBlocks

Этот документ описывает как организованы данные в проекте: папки, файлы, метаданные и их взаимосвязи.

---

## Общая структура папки data/

```text
data/
├── raw/                    сырые CSV файлы с устройства
├── metadata/               метаданные экспериментов и сессий
├── analysis/               результаты анализа качества и графики
├── features/               извлечённые признаки для ML
├── labels/                 справочник типов движений
├── processed/              обработанные данные (зарезервировано)
├── examples/               примеры данных (зарезервировано)
└── db/                     база данных (зарезервировано)
```

---

## Сырые данные — data/raw/

### Структура папок

```text
data/raw/
└── [experiment_id]/
    └── [device_id]/
        └── run_[run_id]_session_[session_id]_[rate]Hz.csv
```

Пример:

```text
data/raw/EXP14/m5-01/run_A_session_A001_100Hz.csv
```

### Имя файла

```text
run_A_session_A001_100Hz.csv
     ↑           ↑      ↑
     run_id    session  частота
```

| Часть | Описание |
|---|---|
| `run_A` | Идентификатор запуска логгера. Назначается логгером при старте. При каждом новом запуске буква увеличивается (A → B → C). Предотвращает перезапись файлов при перезапуске устройства. |
| `session_A001` | Идентификатор сессии с устройства. Устройство всегда начинает с A001. |
| `100Hz` | Частота дискретизации выбранная при запуске. |

### Формат CSV

Каждый файл содержит события и данные одной сессии:

```csv
row_type,session_id,record_id,sample_id,device_timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm,...
EVENT,A001,,,12345,,,,,,,,NEW_SESSION
EVENT,A001,1,,13000,,,,,,,,START
DATA,A001,1,1,13100,0.012,-0.034,0.987,0.12,-0.03,0.01,0.988,...
DATA,A001,1,2,13110,0.015,-0.031,0.991,0.11,-0.02,0.01,0.991,...
EVENT,A001,1,,19000,,,,,,,,STOP
```

### Каналы данных (schema.json)

| Поле | Тип | Единица | Описание |
|---|---|---|---|
| `ax` | acceleration | g | Ускорение по оси X |
| `ay` | acceleration | g | Ускорение по оси Y |
| `az` | acceleration | g | Ускорение по оси Z |
| `gx` | angular_velocity | °/с | Угловая скорость по X |
| `gy` | angular_velocity | °/с | Угловая скорость по Y |
| `gz` | angular_velocity | °/с | Угловая скорость по Z |
| `acc_norm` | derived | g | Норма вектора ускорения √(ax²+ay²+az²) |

В покое `acc_norm ≈ 1.0 g` (сила тяжести). При движении отклоняется.

---

## Метаданные — data/metadata/

### experiments.json

Описание каждого эксперимента. Заполняется вручную после записи.

Пример записи:

```json
{
  "experiment_id": "EXP14",
  "short_name": "EXP14",
  "title": "Сбор первого датасета - 14 июня",
  "started_at": "2026-06-14T12:04:27",
  "location": "Назарьево",
  "environment": "indoor",
  "goal": "Собрать датасет движений для обучения классификатора",
  "participants": ["child_01"],
  "operator_id": "adult_01",
  "device_ids": ["m5-01"],
  "default_device_position": "wrist",
  "default_wrist": "left",
  "default_sample_rate_hz": 100,
  "status": "draft",
  "tags": ["dataset", "classification"]
}
```

Статусы эксперимента:

| Статус | Описание |
|---|---|
| `draft` | Создан автоматически, не заполнен |
| `raw` | Заполнен, данные не проверены |
| `checked` | Данные проверены и пригодны |

---

### recording_sessions.json

Описание каждой записанной сессии. Создаётся автоматически логгером, дополняется вручную.

Пример записи:

```json
{
  "experiment_id": "EXP14",
  "device_id": "m5-01",
  "recording_run_id": "A",
  "device_session_id": "A001",
  "session_uid": "EXP14_m5-01_A_A001",
  "file_name": "run_A_session_A001_100Hz.csv",
  "file_path": "data/raw/EXP14/m5-01/run_A_session_A001_100Hz.csv",
  "firmware_version": "motionblocks.logger.v0.8.0",
  "movement_type": "walking",
  "movement_label": "обычная ходьба",
  "subject_id": "child_01",
  "wrist": "left",
  "started_at": "2026-06-14T12:04:27",
  "sample_rate_hz": 100,
  "status": "checked"
}
```

Поля которые надо заполнять вручную через motion_browser.py:

| Поле | Описание | Пример |
|---|---|---|
| `movement_type` | Тип движения (ключ для ML) | `walking`, `jumping`, `idle` |
| `movement_label` | Описание на русском | `обычная ходьба` |
| `subject_id` | Кто выполнял движение | `child_01`, `adult_01` |
| `wrist` | Рука на которой устройство | `left`, `right` |
| `status` | Статус записи | `draft` → `checked` |

**Важно:** `movement_type` используется как метка класса для обучения ML модели. Без него запись не попадёт в обучающую выборку.

---

### subjects.json

Реестр участников. Никогда не используй реальные имена.

```json
[
  {
    "subject_id": "adult_01",
    "role": "adult",
    "age_group": "adult",
    "dominant_hand": "right",
    "notes": ""
  },
  {
    "subject_id": "child_01",
    "role": "child",
    "age_group": "child",
    "dominant_hand": "right",
    "notes": ""
  }
]
```

Когда добавляется новый участник — добавь запись в этот файл.

Роли: `adult`, `child`, `mentor`

---

### devices.json

Реестр устройств. Создай на основе `devices.example.json`.

```json
[
  {
    "device_id": "m5-01",
    "device_name": "M5StickC Plus2",
    "hardware_model": "M5StickC Plus2",
    "mac_address": "F0:24:F9:97:ED:08",
    "status": "active",
    "notes": ""
  }
]
```

MAC-адрес виден на экране устройства при первом включении или в Serial Monitor в строке `EVENT,DEVICE_INFO`.

---

### feature_config.json

Параметры скользящего окна для `compute_features.py`. Редактировать осторожно — влияет на воспроизводимость ML результатов.

```json
{
  "window_sec": 2.0,
  "step_sec": 0.5,
  "trim_start_sec": 1.0,
  "trim_end_sec": 1.0,
  "acc_norm_rest": 1.0,
  "min_window_fill": 0.7
}
```

| Параметр | Значение | Описание |
|---|---|---|
| `window_sec` | 2.0 | Длина окна в секундах |
| `step_sec` | 0.5 | Шаг между окнами |
| `trim_start_sec` | 1.0 | Обрезка начала записи (убирает артефакт нажатия кнопки) |
| `trim_end_sec` | 1.0 | Обрезка конца записи |
| `min_window_fill` | 0.7 | Минимальная заполненность окна (70%) |

---

### schema.json

Описание каналов IMU данных. Не редактировать — это справочник формата данных.

---

## Результаты анализа — data/analysis/

```text
data/analysis/
└── [experiment_id]/
    ├── session_quality.csv     сводная таблица метрик качества
    └── plots/
        ├── run_A_session_A001_100Hz_acc_norm.png   график нормы ускорения
        └── run_A_session_A001_100Hz_dt_ms.png      график интервалов между сэмплами
```

Генерируется командой:

```powershell
python tools/analyze_recordings.py --experiment EXP14
```

---

## Признаки для ML — data/features/

```text
data/features/
└── [experiment_id]/
    └── features.csv
```

Генерируется командой:

```powershell
python tools/compute_features.py --experiment EXP14
```

`features.csv` содержит одну строку на каждое скользящее окно с вычисленными статистиками (mean, std, max, min, zero-crossings и др.) и меткой `movement_type`.

---

## Идентификаторы — как всё связано

```text
experiment_id   EXP14
device_id       m5-01
recording_run_id  A
device_session_id  A001

→ session_uid = EXP14_m5-01_A_A001
→ file = data/raw/EXP14/m5-01/run_A_session_A001_100Hz.csv
→ metadata в recording_sessions.json
```

---

## Соглашения

- Не использовать реальные имена участников — только `child_01`, `adult_01` и т.д.
- `movement_type` писать на английском, строчными буквами, через подчёркивание: `walking`, `sitting_down`
- Статус `draft` → заполнить метаданные → статус `checked`
- Записи со статусом `draft` не используются для обучения ML

---

## Следующий шаг

→ [03_git-workflow.md](03_git-workflow.md) — как мы работаем с Git
