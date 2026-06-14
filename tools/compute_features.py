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

    # Изменить параметры окна
    python tools/compute_features.py --experiment EXP01 --window-sec 1.0 --step-sec 0.25

Результат:
    data/features/[experiment_id]/features.csv
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------
# Пути
# ------------------------------------------------------------

METADATA_DIR    = Path("data/metadata")
FEATURES_DIR    = Path("data/features")
SESSIONS_PATH   = METADATA_DIR / "recording_sessions.json"
FEATURE_CFG_PATH = METADATA_DIR / "feature_config.json"

# Встроенные дефолты — используются если feature_config.json отсутствует
BUILTIN_DEFAULTS = {
    "window_sec":      2.0,
    "step_sec":        0.5,
    "trim_start_sec":  1.0,
    "trim_end_sec":    1.0,
    "acc_norm_rest":   1.0,
    "min_window_fill": 0.7,
}

ACC_NORM_REST = 1.0  # обновляется из конфига в main()


# ------------------------------------------------------------
# Загрузка данных
# ------------------------------------------------------------

def load_sessions() -> list:
    if not SESSIONS_PATH.exists():
        return []
    return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))


def load_data_rows(csv_path: Path) -> pd.DataFrame:
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
# Фичи одного окна
# ------------------------------------------------------------

def compute_window_features(window: pd.DataFrame, acc_norm_rest: float = 1.0) -> dict:
    feats = {}

    if "acc_norm" in window.columns:
        a = window["acc_norm"].dropna().values
        if len(a) > 0:
            feats["acc_norm_mean"]  = round(float(np.mean(a)), 4)
            feats["acc_norm_std"]   = round(float(np.std(a)), 4)
            feats["acc_norm_max"]   = round(float(np.max(a)), 4)
            feats["acc_norm_min"]   = round(float(np.min(a)), 4)
            feats["acc_norm_range"] = round(float(np.max(a) - np.min(a)), 4)
            centered  = a - acc_norm_rest
            crossings = np.where(np.diff(np.sign(centered)))[0]
            dur_sec   = len(a) / 100.0
            feats["acc_zcr"] = round(len(crossings) / max(dur_sec, 0.001), 2)
        else:
            for k in ["acc_norm_mean", "acc_norm_std", "acc_norm_max",
                      "acc_norm_min", "acc_norm_range", "acc_zcr"]:
                feats[k] = None

    for axis in ["ax", "ay", "az"]:
        if axis in window.columns:
            v = window[axis].dropna().values
            feats[f"{axis}_std"]  = round(float(np.std(v)),  4) if len(v) > 0 else None
            feats[f"{axis}_mean"] = round(float(np.mean(v)), 4) if len(v) > 0 else None

    gyro_cols = [c for c in ["gx", "gy", "gz"] if c in window.columns]
    if gyro_cols:
        gdata = window[gyro_cols].dropna()
        if len(gdata) > 0:
            gnorm = np.sqrt((gdata ** 2).sum(axis=1)).values
            feats["gyro_norm_mean"] = round(float(np.mean(gnorm)), 2)
            feats["gyro_norm_std"]  = round(float(np.std(gnorm)),  2)
            feats["gyro_norm_max"]  = round(float(np.max(gnorm)),  2)
        else:
            feats["gyro_norm_mean"] = feats["gyro_norm_std"] = feats["gyro_norm_max"] = None

    for axis in ["gx", "gy", "gz"]:
        if axis in window.columns:
            v = window[axis].dropna().values
            feats[f"{axis}_std"] = round(float(np.std(v)), 4) if len(v) > 0 else None

    return feats


# ------------------------------------------------------------
# Скользящие окна одной записи
# ------------------------------------------------------------

def extract_record_windows(
    record_data: pd.DataFrame,
    session_info: dict,
    record_id: int,
    cfg: dict,
) -> list:
    if record_data.empty:
        return []

    sample_rate_hz = float(session_info.get("sample_rate_hz", 100) or 100)
    record_data = record_data.sort_values("device_timestamp_ms").reset_index(drop=True)

    t_start = record_data["device_timestamp_ms"].iloc[0]
    t_end   = record_data["device_timestamp_ms"].iloc[-1]
    min_dur = (cfg["trim_start"] + cfg["trim_end"] + cfg["window"]) * 1000

    if (t_end - t_start) < min_dur:
        return []

    trimmed = record_data[
        (record_data["device_timestamp_ms"] >= t_start + cfg["trim_start"] * 1000) &
        (record_data["device_timestamp_ms"] <= t_end   - cfg["trim_end"]   * 1000)
    ].reset_index(drop=True)

    if trimmed.empty:
        return []

    window_ms  = cfg["window"] * 1000
    step_ms    = cfg["step"]   * 1000
    rows = []
    w_start = trimmed["device_timestamp_ms"].iloc[0]
    t_max   = trimmed["device_timestamp_ms"].iloc[-1]
    record_start_ms = t_start  # начало записи до обрезки — точка отсчёта
    win_idx = 0

    while w_start + window_ms <= t_max + 1:
        w_end = w_start + window_ms
        win   = trimmed[
            (trimmed["device_timestamp_ms"] >= w_start) &
            (trimmed["device_timestamp_ms"] <  w_end)
        ]
        if len(win) >= int(sample_rate_hz * cfg["window"] * cfg["min_window_fill"]):
            feats = compute_window_features(win, acc_norm_rest=cfg["acc_norm_rest"])
            row = {
                "experiment_id":     session_info.get("experiment_id", ""),
                "device_id":         session_info.get("device_id", ""),
                "session_uid":       session_info.get("session_uid", ""),
                "recording_run_id":  session_info.get("recording_run_id", ""),
                "device_session_id": session_info.get("device_session_id", ""),
                "record_id":         record_id,
                "window_idx":        win_idx,
                "window_start_ms":   int(w_start),
                "window_end_ms":     int(w_end),
                # Время от начала записи в секундах — удобно для интерпретации
                "time_from_record_start_sec": round(
                    (w_start - record_start_ms) / 1000.0, 2
                ),
                "sample_count":      len(win),
                "sample_rate_hz":    sample_rate_hz,
                "movement_type":     session_info.get("movement_type",  "unknown"),
                "movement_label":    session_info.get("movement_label", "unknown"),
                "subject_id":        session_info.get("subject_id",     "unknown"),
            }
            row.update(feats)
            rows.append(row)
        w_start += step_ms
        win_idx += 1

    return rows


# ------------------------------------------------------------
# Одна сессия
# ------------------------------------------------------------

def extract_session_features(session: dict, cfg: dict) -> list:
    file_path = Path(session.get("file_path", ""))
    if not file_path.exists():
        print(f"  [SKIP] файл не найден: {file_path}")
        return []

    df = load_data_rows(file_path)
    if df.empty:
        return []

    all_rows = []
    if "record_id" in df.columns:
        for rid in sorted(df["record_id"].dropna().unique()):
            rec = df[df["record_id"] == rid].copy()
            all_rows.extend(extract_record_windows(rec, session, int(rid), cfg))
    else:
        all_rows.extend(extract_record_windows(df, session, 0, cfg))

    return all_rows


# ------------------------------------------------------------
# Один эксперимент
# ------------------------------------------------------------

def process_experiment(experiment_id: str, cfg: dict) -> None:
    sessions = load_sessions()
    exp_sessions = [
        s for s in sessions
        if s.get("experiment_id") == experiment_id
        and s.get("movement_type", "unknown") not in ("unknown", "", None)
    ]

    if not exp_sessions:
        print(f"Нет размеченных сессий для {experiment_id}.")
        print("Заполни movement_type в motion_browser.py перед извлечением фич.")
        return

    print(f"\nЭксперимент: {experiment_id}  ({len(exp_sessions)} сессий)")

    all_rows = []
    for s in exp_sessions:
        uid      = s.get("session_uid", "?")
        movement = s.get("movement_type", "?")
        print(f"  {uid}  [{movement}]", end="  ")
        rows = extract_session_features(s, cfg)
        print(f"→ {len(rows)} окон")
        all_rows.extend(rows)

    if not all_rows:
        print("Нет данных для сохранения.")
        return

    df = pd.DataFrame(all_rows)

    print(f"\n  Всего окон: {len(df)}")
    print("  По классам:")
    for cls, cnt in df["movement_type"].value_counts().items():
        print(f"    {cls}: {cnt}")

    out_dir  = FEATURES_DIR / experiment_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "features.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\n  Сохранено: {out_path}")
    print(f"\n  Для Orange Data Mining:")
    print(f"  1. File → Open → {out_path}")
    print(f"  2. Назначить 'movement_type' как целевой класс")
    print(f"  3. kNN или Random Forest → Test & Score")


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def load_feature_config() -> dict:
    """
    Загрузить параметры из feature_config.json.
    Если файл отсутствует — вернуть встроенные дефолты.
    """
    if FEATURE_CFG_PATH.exists():
        try:
            data = json.loads(FEATURE_CFG_PATH.read_text(encoding="utf-8"))
            # Мержим с дефолтами — на случай если в файле нет каких-то полей
            return {**BUILTIN_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] Не удалось прочитать {FEATURE_CFG_PATH}: {e}")
            print("[WARN] Используются встроенные дефолты.")
    return dict(BUILTIN_DEFAULTS)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    # Сначала загружаем конфиг — он даёт дефолты для argparse
    file_cfg = load_feature_config()

    parser = argparse.ArgumentParser(
        description="MotionBlocks Feature Extractor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--experiment", help="experiment_id")
    group.add_argument("--all", action="store_true", help="Все эксперименты")

    parser.add_argument(
        "--window-sec",  type=float,
        default=file_cfg["window_sec"],
        help="Размер окна в секундах"
    )
    parser.add_argument(
        "--step-sec",    type=float,
        default=file_cfg["step_sec"],
        help="Шаг окна в секундах"
    )
    parser.add_argument(
        "--trim-start",  type=float,
        default=file_cfg["trim_start_sec"],
        help="Обрезать начало записи (секунды)"
    )
    parser.add_argument(
        "--trim-end",    type=float,
        default=file_cfg["trim_end_sec"],
        help="Обрезать конец записи (секунды)"
    )
    parser.add_argument(
        "--acc-norm-rest", type=float,
        default=file_cfg["acc_norm_rest"],
        help="Уровень покоя для zero-crossing (g)"
    )
    parser.add_argument(
        "--min-window-fill", type=float,
        default=file_cfg["min_window_fill"],
        help="Минимальная заполненность окна (0.0–1.0)"
    )

    args = parser.parse_args()

    # Финальный конфиг — дефолты из файла + CLI переопределения
    cfg = {
        "window":          args.window_sec,
        "step":            args.step_sec,
        "trim_start":      args.trim_start,
        "trim_end":        args.trim_end,
        "acc_norm_rest":   args.acc_norm_rest,
        "min_window_fill": args.min_window_fill,
    }

    # Обновляем глобальную константу для compute_window_features
    global ACC_NORM_REST
    ACC_NORM_REST = cfg["acc_norm_rest"]

    source = f"{FEATURE_CFG_PATH}" if FEATURE_CFG_PATH.exists() else "встроенные дефолты"
    print(f"Конфиг: {source}")
    print(f"  окно={cfg['window']}s  шаг={cfg['step']}s  "
          f"обрезка={cfg['trim_start']}s+{cfg['trim_end']}s  "
          f"acc_norm_rest={cfg['acc_norm_rest']}g  "
          f"min_fill={cfg['min_window_fill']}")

    if args.experiment:
        process_experiment(args.experiment, cfg)
    elif args.all:
        sessions = load_sessions()
        exp_ids  = sorted(set(
            s.get("experiment_id", "")
            for s in sessions if s.get("experiment_id")
        ))
        for exp_id in exp_ids:
            process_experiment(exp_id, cfg)


if __name__ == "__main__":
    main()
