"""
MotionBlocks — Feature Extractor
tools/compute_features.py

Назначение:
    Извлечение фич из сырых CSV файлов для ML эксперимента.
    Выходной файл features.csv содержит одну строку на скользящее окно.

Параметры окна:
    window_sec  = 2.0s   (размер окна)
    step_sec    = 0.5s   (шаг — перекрытие 75%)
    trim_start  = 1.0s   (обрезать начало записи — артефакт кнопки)
    trim_end    = 1.0s   (обрезать конец записи — артефакт кнопки)

Использование:

    # Один эксперимент
    python tools/compute_features.py --experiment EXP01

    # Все эксперименты
    python tools/compute_features.py --all

Результат:
    data/features/[experiment_id]/features.csv
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------
# Конфигурация
# ------------------------------------------------------------

METADATA_DIR  = Path("data/metadata")
RAW_DIR       = Path("data/raw")
FEATURES_DIR  = Path("data/features")
SESSIONS_PATH = METADATA_DIR / "recording_sessions.json"

TRIM_START_SEC = 1.0   # обрезать начало записи
TRIM_END_SEC   = 1.0   # обрезать конец записи
WINDOW_SEC     = 2.0   # размер окна
STEP_SEC       = 0.5   # шаг окна

# Порог для zero-crossing относительно покоя (1g)
ACC_NORM_REST  = 1.0


# ------------------------------------------------------------
# Загрузка данных
# ------------------------------------------------------------

def load_sessions() -> list[dict]:
    if not SESSIONS_PATH.exists():
        return []
    return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))


def load_data_rows(csv_path: Path) -> pd.DataFrame:
    """Загрузить только DATA строки из CSV, привести к числовым типам."""
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if df.empty:
        return pd.DataFrame()

    if "row_type" in df.columns:
        df = df[df["row_type"] == "DATA"].copy()

    for col in ["device_timestamp_ms", "record_id", "sample_id",
                "ax", "ay", "az", "gx", "gy", "gz", "acc_norm"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.reset_index(drop=True)


# ------------------------------------------------------------
# Расчёт фич для одного окна
# ------------------------------------------------------------

def compute_window_features(window: pd.DataFrame) -> dict:
    """
    Рассчитать фичи для одного временного окна.

    Простые статистические фичи по acc_norm, gyro_norm и осям.
    Достаточно для разделения idle / walking / jumping / shake.
    """
    features = {}

    # acc_norm фичи
    if "acc_norm" in window.columns:
        a = window["acc_norm"].dropna().values
        if len(a) > 0:
            features["acc_norm_mean"] = round(float(np.mean(a)), 4)
            features["acc_norm_std"]  = round(float(np.std(a)), 4)
            features["acc_norm_max"]  = round(float(np.max(a)), 4)
            features["acc_norm_min"]  = round(float(np.min(a)), 4)
            features["acc_norm_range"] = round(float(np.max(a) - np.min(a)), 4)

            # Zero-crossing rate относительно уровня покоя 1g
            # Считаем сколько раз сигнал пересекает ACC_NORM_REST
            centered = a - ACC_NORM_REST
            crossings = np.where(np.diff(np.sign(centered)))[0]
            duration_sec = len(a) / 100.0  # приблизительно при 100 Hz
            features["acc_zcr"] = round(
                len(crossings) / max(duration_sec, 0.001), 2
            )
        else:
            for k in ["acc_norm_mean", "acc_norm_std", "acc_norm_max",
                      "acc_norm_min", "acc_norm_range", "acc_zcr"]:
                features[k] = None

    # Фичи по отдельным осям акселерометра
    for axis in ["ax", "ay", "az"]:
        if axis in window.columns:
            v = window[axis].dropna().values
            features[f"{axis}_std"]  = round(float(np.std(v)), 4) if len(v) > 0 else None
            features[f"{axis}_mean"] = round(float(np.mean(v)), 4) if len(v) > 0 else None

    # gyro_norm фичи
    gyro_cols = [c for c in ["gx", "gy", "gz"] if c in window.columns]
    if gyro_cols:
        gyro_data = window[gyro_cols].dropna()
        if len(gyro_data) > 0:
            gyro_norm = np.sqrt((gyro_data ** 2).sum(axis=1)).values
            features["gyro_norm_mean"] = round(float(np.mean(gyro_norm)), 2)
            features["gyro_norm_std"]  = round(float(np.std(gyro_norm)), 2)
            features["gyro_norm_max"]  = round(float(np.max(gyro_norm)), 2)
        else:
            features["gyro_norm_mean"] = None
            features["gyro_norm_std"]  = None
            features["gyro_norm_max"]  = None

    # Фичи по отдельным осям гироскопа
    for axis in ["gx", "gy", "gz"]:
        if axis in window.columns:
            v = window[axis].dropna().values
            features[f"{axis}_std"] = round(float(np.std(v)), 4) if len(v) > 0 else None

    return features


# ------------------------------------------------------------
# Обработка одной записи (record_id)
# ------------------------------------------------------------

def extract_record_windows(
    record_data: pd.DataFrame,
    session_info: dict,
    record_id: int,
    sample_rate_hz: float,
) -> list[dict]:
    """
    Извлечь окна из одной записи.

    1. Обрезать начало и конец (артефакты кнопки).
    2. Нарезать скользящими окнами.
    3. Рассчитать фичи для каждого окна.
    """
    if record_data.empty:
        return []

    # Сортируем по времени
    record_data = record_data.sort_values("device_timestamp_ms").reset_index(drop=True)

    t_start = record_data["device_timestamp_ms"].iloc[0]
    t_end   = record_data["device_timestamp_ms"].iloc[-1]
    duration_ms = t_end - t_start

    # Минимальная длительность после обрезки
    min_duration_ms = (TRIM_START_SEC + TRIM_END_SEC + WINDOW_SEC) * 1000
    if duration_ms < min_duration_ms:
        return []

    # Обрезаем края
    t_trim_start = t_start + TRIM_START_SEC * 1000
    t_trim_end   = t_end   - TRIM_END_SEC   * 1000

    trimmed = record_data[
        (record_data["device_timestamp_ms"] >= t_trim_start) &
        (record_data["device_timestamp_ms"] <= t_trim_end)
    ].reset_index(drop=True)

    if trimmed.empty:
        return []

    # Параметры окна в миллисекундах
    window_ms = WINDOW_SEC * 1000
    step_ms   = STEP_SEC   * 1000

    windows = []
    window_idx = 0
    w_start_ms = trimmed["device_timestamp_ms"].iloc[0]
    t_max = trimmed["device_timestamp_ms"].iloc[-1]

    while w_start_ms + window_ms <= t_max + 1:
        w_end_ms = w_start_ms + window_ms

        window = trimmed[
            (trimmed["device_timestamp_ms"] >= w_start_ms) &
            (trimmed["device_timestamp_ms"] <  w_end_ms)
        ]

        if len(window) >= int(sample_rate_hz * WINDOW_SEC * 0.7):
            # Достаточно сэмплов (минимум 70% от ожидаемого)
            feats = compute_window_features(window)

            row = {
                # Идентификаторы для трассировки
                "experiment_id":  session_info.get("experiment_id", ""),
                "device_id":      session_info.get("device_id", ""),
                "session_uid":    session_info.get("session_uid", ""),
                "recording_run_id": session_info.get("recording_run_id", ""),
                "device_session_id": session_info.get("device_session_id", ""),
                "record_id":      record_id,
                "window_idx":     window_idx,
                "window_start_ms": int(w_start_ms),
                "window_end_ms":   int(w_end_ms),
                "sample_count":   len(window),
                "sample_rate_hz": sample_rate_hz,
                # Метаданные движения (целевой класс)
                "movement_type":  session_info.get("movement_type", "unknown"),
                "movement_label": session_info.get("movement_label", "unknown"),
                "subject_id":     session_info.get("subject_id", "unknown"),
            }
            row.update(feats)
            windows.append(row)

        w_start_ms += step_ms
        window_idx += 1

    return windows


# ------------------------------------------------------------
# Обработка одной сессии
# ------------------------------------------------------------

def extract_session_features(session: dict) -> list[dict]:
    """Извлечь фичи из всех записей одной сессии."""
    file_path = Path(session.get("file_path", ""))
    if not file_path.exists():
        print(f"  [SKIP] файл не найден: {file_path}")
        return []

    sample_rate_hz = float(session.get("sample_rate_hz", 100))

    # Пробуем вытащить Hz из имени файла если нет в метаданных
    if not sample_rate_hz and "Hz" in file_path.name:
        try:
            sample_rate_hz = float(file_path.stem.split("_")[-1].replace("Hz", ""))
        except (ValueError, IndexError):
            sample_rate_hz = 100.0

    df = load_data_rows(file_path)
    if df.empty:
        return []

    all_windows = []

    if "record_id" in df.columns:
        record_ids = sorted(df["record_id"].dropna().unique())
        for rid in record_ids:
            record_data = df[df["record_id"] == rid].copy()
            windows = extract_record_windows(
                record_data, session, int(rid), sample_rate_hz
            )
            all_windows.extend(windows)
    else:
        # Нет record_id — обрабатываем как одну запись
        windows = extract_record_windows(df, session, 0, sample_rate_hz)
        all_windows.extend(windows)

    return all_windows


# ------------------------------------------------------------
# Основная логика
# ------------------------------------------------------------

def process_experiment(experiment_id: str) -> None:
    sessions = load_sessions()
    exp_sessions = [
        s for s in sessions
        if s.get("experiment_id") == experiment_id
        and s.get("movement_type", "unknown") != "unknown"
    ]

    if not exp_sessions:
        print(f"Нет размеченных сессий для {experiment_id}")
        print("Заполни movement_type в motion_browser.py перед извлечением фич.")
        return

    print(f"\nЭксперимент: {experiment_id}  ({len(exp_sessions)} сессий)")

    all_rows = []
    for session in exp_sessions:
        uid = session.get("session_uid", "?")
        movement = session.get("movement_type", "?")
        print(f"  {uid}  [{movement}]", end="  ")

        rows = extract_session_features(session)
        print(f"→ {len(rows)} окон")
        all_rows.extend(rows)

    if not all_rows:
        print("Нет данных для сохранения.")
        return

    df = pd.DataFrame(all_rows)

    # Сводка по классам
    print(f"\n  Всего окон: {len(df)}")
    print("  Окон по классам:")
    counts = df["movement_type"].value_counts()
    for cls, cnt in counts.items():
        print(f"    {cls}: {cnt}")

    # Сохраняем
    output_dir = FEATURES_DIR / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n  Saved: {output_path}")

    # Краткая сводка для Orange
    print(f"\n  Для Orange Data Mining:")
    print(f"  1. File → Open → {output_path}")
    print(f"  2. Поставить 'movement_type' как целевой класс (target)")
    print(f"  3. Блоки: kNN или Random Forest → Test & Score")


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="MotionBlocks Feature Extractor"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--experiment", help="experiment_id")
    group.add_argument("--all",        action="store_true",
                       help="Все эксперименты")

    parser.add_argument("--window-sec", type=float, default=WINDOW_SEC)
    parser.add_argument("--step-sec",   type=float, default=STEP_SEC)
    parser.add_argument("--trim-start", type=float, default=TRIM_START_SEC)
    parser.add_argument("--trim-end",   type=float, default=TRIM_END_SEC)

    args = parser.parse_args()

    # Применяем параметры из CLI если переданы
    global WINDOW_SEC, STEP_SEC, TRIM_START_SEC, TRIM_END_SEC  # noqa: PLW0603
    WINDOW_SEC     = args.window_sec
    STEP_SEC       = args.step_sec
    TRIM_START_SEC = args.trim_start
    TRIM_END_SEC   = args.trim_end

    print(f"Параметры окна: {WINDOW_SEC}s / шаг {STEP_SEC}s / "
          f"обрезка {TRIM_START_SEC}s + {TRIM_END_SEC}s")

    if args.experiment:
        process_experiment(args.experiment)
    elif args.all:
        sessions  = load_sessions()
        exp_ids   = sorted(set(
            s.get("experiment_id", "")
            for s in sessions
            if s.get("experiment_id")
        ))
        for exp_id in exp_ids:
            process_experiment(exp_id)


if __name__ == "__main__":
    main()
