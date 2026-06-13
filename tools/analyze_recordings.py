"""
MotionBlocks — Recording Analyzer
tools/analyze_recordings.py

Назначение:
    Анализ качества записей и расчёт базовых метрик.

Использование:

    # Один файл
    python tools/analyze_recordings.py --file data/raw/EXP10/m5-01/run_A_session_A001_100Hz.csv

    # Все файлы одного эксперимента
    python tools/analyze_recordings.py --experiment EXP10

    # Все файлы всех экспериментов
    python tools/analyze_recordings.py --all

Результаты сохраняются в:
    data/analysis/[experiment_id]/session_quality.csv
    data/analysis/[experiment_id]/plots/[file_name]_acc_norm.png
    data/analysis/[experiment_id]/plots/[file_name]_dt_ms.png
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # без GUI — для сохранения в файл
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ------------------------------------------------------------
# Конфигурация
# ------------------------------------------------------------

METADATA_DIR   = Path("data/metadata")
RAW_DIR        = Path("data/raw")
ANALYSIS_DIR   = Path("data/analysis")
SESSIONS_PATH  = METADATA_DIR / "recording_sessions.json"

# Порог для определения gap — интервал больше 3x ожидаемого dt
GAP_THRESHOLD_FACTOR = 3.0

# Минимальная длительность записи для статуса OK (секунды)
MIN_DURATION_SEC = 1.0

# Допустимое отклонение effective rate от configured (%)
RATE_TOLERANCE_PCT = 20.0


# ------------------------------------------------------------
# Загрузка данных
# ------------------------------------------------------------

def load_sessions() -> list[dict]:
    if not SESSIONS_PATH.exists():
        return []
    return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


def get_data_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Извлечь только DATA строки и привести к числовым типам."""
    if df.empty:
        return pd.DataFrame()

    if "row_type" in df.columns:
        data = df[df["row_type"] == "DATA"].copy()
    else:
        data = df.copy()

    for col in ["device_timestamp_ms", "ax", "ay", "az",
                "gx", "gy", "gz", "acc_norm", "record_id", "sample_id"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    return data.reset_index(drop=True)


# ------------------------------------------------------------
# Расчёт метрик
# ------------------------------------------------------------

def analyze_file(
    csv_path: Path,
    configured_hz: float = None,
    session_uid: str = None,
) -> dict:
    """
    Рассчитать метрики качества для одного CSV файла.

    Возвращает словарь с метриками.
    """
    result = {
        "file_name":              csv_path.name,
        "file_path":              csv_path.as_posix(),
        "session_uid":            session_uid or "",
        "configured_hz":          configured_hz,
        "total_rows":             0,
        "data_rows":              0,
        "records":                0,
        "duration_sec":           None,
        "effective_hz":           None,
        "mean_dt_ms":             None,
        "median_dt_ms":           None,
        "min_dt_ms":              None,
        "max_dt_ms":              None,
        "p95_dt_ms":              None,
        "gap_count":              0,
        "acc_norm_mean":          None,
        "acc_norm_std":           None,
        "acc_norm_max":           None,
        "gyro_norm_mean":         None,
        "gyro_norm_max":          None,
        "quality_status":         "BAD_EMPTY",
        "quality_notes":          [],
    }

    df = load_csv(csv_path)
    if df.empty:
        return result

    result["total_rows"] = len(df)
    data = get_data_rows(df)

    if data.empty:
        return result

    result["data_rows"] = len(data)
    result["records"]   = int(data["record_id"].nunique()) \
        if "record_id" in data.columns else 0

    # --- Временные метрики (считаем внутри каждой записи) ---
    if "device_timestamp_ms" in data.columns:
        t_all = data["device_timestamp_ms"].dropna()

        if len(t_all) > 1:
            duration_ms  = t_all.max() - t_all.min()
            duration_sec = duration_ms / 1000.0
            result["duration_sec"] = round(duration_sec, 2)

        # dt_ms считаем только внутри каждого record_id
        # чтобы межзаписные паузы не попадали в статистику
        if "record_id" in data.columns:
            dt_parts = []
            for rid, group in data.groupby("record_id"):
                t = group["device_timestamp_ms"].dropna().sort_values()
                if len(t) > 1:
                    dt_parts.append(t.diff().dropna())
            dt = pd.concat(dt_parts) if dt_parts else pd.Series(dtype=float)
        else:
            t_sorted = t_all.sort_values()
            dt = t_sorted.diff().dropna()

        if len(dt) > 0:
            result["mean_dt_ms"]   = round(float(dt.mean()), 2)
            result["median_dt_ms"] = round(float(dt.median()), 2)
            result["min_dt_ms"]    = round(float(dt.min()), 2)
            result["max_dt_ms"]    = round(float(dt.max()), 2)
            result["p95_dt_ms"]    = round(float(dt.quantile(0.95)), 2)

            # Effective Hz считаем из суммарной длительности всех записей
            if "record_id" in data.columns:
                total_samples = 0
                total_dur_ms  = 0.0
                for rid, group in data.groupby("record_id"):
                    t = group["device_timestamp_ms"].dropna().sort_values()
                    if len(t) > 1:
                        total_samples += len(t) - 1
                        total_dur_ms  += t.max() - t.min()
                if total_dur_ms > 0:
                    result["effective_hz"] = round(total_samples / (total_dur_ms / 1000), 1)
            else:
                if duration_sec and duration_sec > 0:
                    result["effective_hz"] = round((len(t_all) - 1) / duration_sec, 1)

            # Gaps — только внутри записей
            if configured_hz:
                expected_dt   = 1000.0 / configured_hz
                gap_threshold = expected_dt * GAP_THRESHOLD_FACTOR
            else:
                gap_threshold = float(dt.median()) * GAP_THRESHOLD_FACTOR

            result["gap_count"] = int((dt > gap_threshold).sum())

    # --- Акселерометр ---
    if "acc_norm" in data.columns:
        acc = data["acc_norm"].dropna()
        if len(acc) > 0:
            result["acc_norm_mean"] = round(float(acc.mean()), 4)
            result["acc_norm_std"]  = round(float(acc.std()), 4)
            result["acc_norm_max"]  = round(float(acc.max()), 4)

    # --- Гироскоп ---
    gyro_cols = [c for c in ["gx", "gy", "gz"] if c in data.columns]
    if gyro_cols:
        gyro_data = data[gyro_cols].dropna()
        if len(gyro_data) > 0:
            gyro_norm = np.sqrt((gyro_data ** 2).sum(axis=1))
            result["gyro_norm_mean"] = round(float(gyro_norm.mean()), 2)
            result["gyro_norm_max"]  = round(float(gyro_norm.max()), 2)

    # --- Quality status ---
    notes = []
    status = "OK"

    if result["data_rows"] == 0:
        status = "BAD_EMPTY"
        notes.append("no DATA rows")

    elif result["duration_sec"] is not None and result["duration_sec"] < MIN_DURATION_SEC:
        status = "WARN_SHORT"
        notes.append(f"duration {result['duration_sec']:.1f}s < {MIN_DURATION_SEC}s")

    else:
        if result["gap_count"] and result["gap_count"] > 0:
            status = "WARN_GAPS"
            notes.append(f"{result['gap_count']} gaps detected")

        if configured_hz and result["effective_hz"]:
            deviation_pct = abs(result["effective_hz"] - configured_hz) / configured_hz * 100
            if deviation_pct > RATE_TOLERANCE_PCT:
                if status == "OK":
                    status = "WARN_RATE_MISMATCH"
                notes.append(
                    f"effective {result['effective_hz']}Hz vs configured {configured_hz}Hz "
                    f"({deviation_pct:.0f}% deviation)"
                )

    result["quality_status"] = status
    result["quality_notes"]  = "; ".join(notes) if notes else "—"

    return result


# ------------------------------------------------------------
# Графики
# ------------------------------------------------------------

def plot_acc_norm(data: pd.DataFrame, title: str, output_path: Path,
                  configured_hz: float = None) -> None:
    """Сохранить график acc_norm по записям."""
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_title(f"acc_norm — {title}", fontsize=11)
    ax.set_ylabel("g")
    ax.axhline(1.0, color="grey", lw=0.8, ls="--", alpha=0.6, label="1g (покой)")

    if "record_id" in data.columns:
        record_ids = sorted(data["record_id"].dropna().unique())
        colors = plt.cm.tab10.colors

        for i, rid in enumerate(record_ids):
            sub = data[data["record_id"] == rid].copy()
            if "device_timestamp_ms" in sub.columns:
                t = sub["device_timestamp_ms"] - sub["device_timestamp_ms"].min()
                ax.plot(t, sub["acc_norm"], lw=0.8,
                        color=colors[i % len(colors)], label=f"R{int(rid)}")
                ax.set_xlabel("Время от начала записи (ms)")
            else:
                ax.plot(sub["acc_norm"].values, lw=0.8,
                        color=colors[i % len(colors)], label=f"R{int(rid)}")
                ax.set_xlabel("Индекс сэмпла")
    else:
        ax.plot(data["acc_norm"].values, lw=0.8, color="steelblue")
        ax.set_xlabel("Индекс сэмпла")

    ax.legend(fontsize=8, loc="upper right")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


def plot_dt_ms(data: pd.DataFrame, title: str, output_path: Path,
               configured_hz: float = None) -> None:
    """Сохранить график dt_ms — интервалы между сэмплами."""
    if "device_timestamp_ms" not in data.columns:
        return

    fig, ax = plt.subplots(figsize=(14, 3))
    ax.set_title(f"dt_ms — {title}", fontsize=11)
    ax.set_ylabel("ms")
    ax.set_xlabel("Индекс сэмпла")

    if configured_hz:
        expected = 1000.0 / configured_hz
        ax.axhline(expected, color="grey", lw=0.8, ls="--",
                   label=f"ожидаемый {expected:.0f}ms")

    if "record_id" in data.columns:
        record_ids = sorted(data["record_id"].dropna().unique())
        colors = plt.cm.tab10.colors
        offset = 0
        for i, rid in enumerate(record_ids):
            sub = data[data["record_id"] == rid].copy()
            dt = sub["device_timestamp_ms"].diff().dropna()
            idx = range(offset, offset + len(dt))
            ax.plot(list(idx), dt.values, lw=0.8,
                    color=colors[i % len(colors)], label=f"R{int(rid)}")
            offset += len(sub)
    else:
        dt = data["device_timestamp_ms"].diff().dropna()
        ax.plot(dt.values, lw=0.8, color="steelblue")

    ax.legend(fontsize=8, loc="upper right")
    # Ограничиваем ось Y по данным внутри записей (без межзаписных пауз)
    if "record_id" in data.columns:
        dt_parts = []
        for rid, group in data.groupby("record_id"):
            t = group["device_timestamp_ms"].dropna().sort_values()
            if len(t) > 1:
                dt_parts.append(t.diff().dropna())
        dt_all = pd.concat(dt_parts) if dt_parts else data["device_timestamp_ms"].diff().dropna()
    else:
        dt_all = data["device_timestamp_ms"].diff().dropna()
    p99 = float(dt_all.quantile(0.99))
    ax.set_ylim(0, max(p99 * 2, 50))

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


# ------------------------------------------------------------
# Вывод результата в консоль
# ------------------------------------------------------------

def print_result(r: dict) -> None:
    status_emoji = {
        "OK":                "✅",
        "WARN_GAPS":         "⚠️ ",
        "WARN_SHORT":        "⚠️ ",
        "WARN_RATE_MISMATCH":"⚠️ ",
        "BAD_EMPTY":         "❌",
    }.get(r["quality_status"], "?")

    print(f"\n{'─'*60}")
    print(f"  {status_emoji} {r['quality_status']:20s}  {r['file_name']}")
    print(f"{'─'*60}")
    print(f"  Строк всего:      {r['total_rows']}")
    print(f"  DATA строк:       {r['data_rows']}")
    print(f"  Записей:          {r['records']}")

    if r["duration_sec"] is not None:
        print(f"  Длительность:     {r['duration_sec']:.1f} s")

    if r["configured_hz"]:
        print(f"  Частота (config): {r['configured_hz']} Hz")

    if r["effective_hz"]:
        print(f"  Частота (факт):   {r['effective_hz']} Hz")

    if r["mean_dt_ms"]:
        print(f"  dt_ms mean/med:   {r['mean_dt_ms']} / {r['median_dt_ms']} ms")
        print(f"  dt_ms min/max:    {r['min_dt_ms']} / {r['max_dt_ms']} ms")
        print(f"  dt_ms p95:        {r['p95_dt_ms']} ms")

    print(f"  Gaps:             {r['gap_count']}")

    if r["acc_norm_mean"]:
        print(f"  acc_norm mean:    {r['acc_norm_mean']} g  (std {r['acc_norm_std']})")
        print(f"  acc_norm max:     {r['acc_norm_max']} g")

    if r["gyro_norm_mean"]:
        print(f"  gyro_norm mean:   {r['gyro_norm_mean']} deg/s")
        print(f"  gyro_norm max:    {r['gyro_norm_max']} deg/s")

    if r["quality_notes"] != "—":
        print(f"  Заметки:          {r['quality_notes']}")


# ------------------------------------------------------------
# Сохранение session_quality.csv
# ------------------------------------------------------------

def save_quality_csv(results: list[dict], experiment_id: str) -> Path:
    output_dir = ANALYSIS_DIR / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "session_quality.csv"

    # Убираем поля которые не нужны в CSV
    rows = []
    for r in results:
        row = {k: v for k, v in r.items()}
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


# ------------------------------------------------------------
# Основная логика анализа
# ------------------------------------------------------------

def analyze_single_file(csv_path: Path, save_plots: bool = True) -> dict:
    """Анализ одного файла."""

    # Пробуем найти metadata для этого файла
    sessions = load_sessions()
    session  = next(
        (s for s in sessions if s.get("file_name") == csv_path.name),
        None
    )

    configured_hz = None
    session_uid   = None

    if session:
        configured_hz = session.get("sample_rate_hz")
        session_uid   = session.get("session_uid")

    # Пробуем вытащить Hz из имени файла если нет в metadata
    if not configured_hz and "Hz" in csv_path.name:
        try:
            hz_part = csv_path.stem.split("_")[-1].replace("Hz", "")
            configured_hz = float(hz_part)
        except (ValueError, IndexError):
            pass

    result = analyze_file(csv_path, configured_hz=configured_hz, session_uid=session_uid)
    print_result(result)

    if save_plots:
        df     = load_csv(csv_path)
        data   = get_data_rows(df)
        exp_id = session.get("experiment_id", "unknown") if session else "unknown"
        plots_dir = ANALYSIS_DIR / exp_id / "plots"

        if "acc_norm" in data.columns:
            out = plots_dir / f"{csv_path.stem}_acc_norm.png"
            plot_acc_norm(data, csv_path.name, out, configured_hz)
            print(f"  Plot: {out}")

        if "device_timestamp_ms" in data.columns:
            out = plots_dir / f"{csv_path.stem}_dt_ms.png"
            plot_dt_ms(data, csv_path.name, out, configured_hz)
            print(f"  Plot: {out}")

    return result


def analyze_experiment(experiment_id: str) -> list[dict]:
    """Анализ всех файлов одного эксперимента."""
    sessions = load_sessions()
    exp_sessions = [s for s in sessions if s.get("experiment_id") == experiment_id]

    if not exp_sessions:
        print(f"Нет сессий для эксперимента {experiment_id}")
        return []

    print(f"\n{'='*60}")
    print(f"  Эксперимент: {experiment_id}  ({len(exp_sessions)} сессий)")
    print(f"{'='*60}")

    results = []
    for session in exp_sessions:
        file_path = Path(session.get("file_path", ""))
        if not file_path.exists():
            print(f"\n  [SKIP] файл не найден: {file_path}")
            continue

        configured_hz = session.get("sample_rate_hz")
        session_uid   = session.get("session_uid")

        result = analyze_file(file_path, configured_hz=configured_hz,
                              session_uid=session_uid)
        print_result(result)

        # Графики
        df   = load_csv(file_path)
        data = get_data_rows(df)
        plots_dir = ANALYSIS_DIR / experiment_id / "plots"

        if "acc_norm" in data.columns:
            out = plots_dir / f"{file_path.stem}_acc_norm.png"
            plot_acc_norm(data, file_path.name, out, configured_hz)

        if "device_timestamp_ms" in data.columns:
            out = plots_dir / f"{file_path.stem}_dt_ms.png"
            plot_dt_ms(data, file_path.name, out, configured_hz)

        results.append(result)

    if results:
        quality_path = save_quality_csv(results, experiment_id)
        print(f"\n  Quality report: {quality_path}")

        # Сводка
        print(f"\n  Сводка по {experiment_id}:")
        statuses = pd.Series([r["quality_status"] for r in results]).value_counts()
        for status, count in statuses.items():
            print(f"    {status}: {count}")

    return results


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MotionBlocks Recording Analyzer")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file",       help="Путь к одному CSV файлу")
    group.add_argument("--experiment", help="experiment_id для анализа всех сессий")
    group.add_argument("--all",        action="store_true",
                       help="Анализ всех экспериментов")

    parser.add_argument("--no-plots", action="store_true",
                        help="Не сохранять графики")

    args = parser.parse_args()

    if args.file:
        analyze_single_file(Path(args.file), save_plots=not args.no_plots)

    elif args.experiment:
        analyze_experiment(args.experiment)

    elif args.all:
        sessions  = load_sessions()
        exp_ids   = sorted(set(s.get("experiment_id", "") for s in sessions if s.get("experiment_id")))
        print(f"Найдено экспериментов: {len(exp_ids)}")
        for exp_id in exp_ids:
            analyze_experiment(exp_id)


if __name__ == "__main__":
    main()
