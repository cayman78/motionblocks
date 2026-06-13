"""
MotionBlocks — Metadata Migration
tools/migrate_metadata.py

Мигрирует существующие metadata файлы в новый формат v2.

Изменения:
  experiments.json:
    - status "auto created. needs description." -> "draft"
    - ended_at вычисляется из recording_sessions (если null)

  recording_sessions.json:
    - убираем: file_role, mac_address, hardware_model, records_expected,
                session_id (дубль), channels, tags
    - добавляем: wrist (наследуется из эксперимента)
    - status "auto created. needs description." -> "draft"

  devices.json:
    - без изменений, только копируем

  НОВЫЕ ФАЙЛЫ:
    subjects.json   — создаётся с известными субъектами
    schema.json     — выносим channels из сессий

Запуск:
    python tools/migrate_metadata.py

Резервная копия создаётся автоматически в:
    data/metadata/backup_YYYYMMDD_HHMMSS/
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

METADATA_DIR = Path("data/metadata")

EXPERIMENTS_PATH = METADATA_DIR / "experiments.json"
SESSIONS_PATH    = METADATA_DIR / "recording_sessions.json"
DEVICES_PATH     = METADATA_DIR / "devices.json"
SUBJECTS_PATH    = METADATA_DIR / "subjects.json"
SCHEMA_PATH      = METADATA_DIR / "schema.json"

OLD_AUTO_STATUS = "auto created. needs description."
NEW_DRAFT_STATUS = "draft"


def load_json(path: Path) -> list | dict:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return json.loads(text)


def save_json(path: Path, data: list | dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Saved: {path}")


def make_backup() -> Path:
    """Создать резервную копию всей папки metadata."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = METADATA_DIR / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for f in METADATA_DIR.iterdir():
        if f.is_file() and f.suffix == ".json":
            shutil.copy2(f, backup_dir / f.name)

    print(f"  Backup created: {backup_dir}")
    return backup_dir


def migrate_experiments(experiments: list, sessions: list) -> list:
    """Мигрировать experiments.json."""

    # Собираем максимальный started_at по сессиям для каждого эксперимента
    # чтобы вычислить ended_at
    session_dates: dict[str, list[str]] = {}
    for s in sessions:
        exp_id = s.get("experiment_id")
        started = s.get("started_at")
        if exp_id and started:
            session_dates.setdefault(exp_id, []).append(started)

    migrated = []
    for exp in experiments:
        e = dict(exp)

        # Статус
        if e.get("status") == OLD_AUTO_STATUS:
            e["status"] = NEW_DRAFT_STATUS

        # ended_at — вычисляем если null
        if e.get("ended_at") is None:
            exp_id = e.get("experiment_id")
            dates = session_dates.get(exp_id, [])
            if dates:
                e["ended_at"] = max(dates)

        # participants — убеждаемся что это список
        if isinstance(e.get("participants"), str):
            e["participants"] = [e["participants"]] if e["participants"] else []

        migrated.append(e)

    return migrated


def migrate_sessions(sessions: list, experiments: list) -> list:
    """Мигрировать recording_sessions.json."""

    # Индекс экспериментов для наследования wrist
    exp_index = {e["experiment_id"]: e for e in experiments}

    # Поля которые убираем
    fields_to_remove = {
        "file_role",
        "mac_address",
        "hardware_model",
        "records_expected",
        "session_id",       # дубль device_session_id
        "channels",
        "tags",
        "file_id",
        "device_name",      # в devices.json
    }

    migrated = []
    for s in sessions:
        row = {}

        # Копируем нужные поля в правильном порядке
        ordered_fields = [
            "experiment_id",
            "device_id",
            "recording_run_id",
            "device_session_id",
            "session_uid",
            "file_name",
            "file_path",
            "data_format",
            "schema_version",
            "firmware_version",
            "movement_type",
            "movement_label",
            "subject_id",
            "wrist",
            "started_at",
            "sample_rate_hz",
            "records_actual",
            "comment",
            "status",
        ]

        for field in ordered_fields:
            if field in fields_to_remove:
                continue

            if field == "wrist":
                # Берём из сессии если есть, иначе из эксперимента
                wrist = s.get("wrist")
                if not wrist:
                    exp = exp_index.get(s.get("experiment_id", ""), {})
                    wrist = exp.get("default_wrist")
                row["wrist"] = wrist
                continue

            if field == "device_session_id":
                # Если нет device_session_id — берём из session_id
                val = s.get("device_session_id") or s.get("session_id")
                row["device_session_id"] = val
                continue

            if field in s:
                row[field] = s[field]
            else:
                # Дефолты для новых полей
                if field == "recording_run_id":
                    row[field] = None
                elif field == "records_actual":
                    row[field] = None
                elif field == "firmware_version":
                    row[field] = None

        # Статус
        if row.get("status") == OLD_AUTO_STATUS:
            row["status"] = NEW_DRAFT_STATUS

        migrated.append(row)

    return migrated


def create_schema() -> dict:
    """Создать schema.json с описанием каналов IMU."""
    return {
        "schema_version": "motionblocks.sample.v0.1",
        "description": "MotionBlocks IMU schema — M5StickC Plus2, 6-axis IMU + derived acc_norm",
        "channels": [
            {"name": "ax", "kind": "acceleration", "axis": "x", "unit": "g"},
            {"name": "ay", "kind": "acceleration", "axis": "y", "unit": "g"},
            {"name": "az", "kind": "acceleration", "axis": "z", "unit": "g"},
            {"name": "gx", "kind": "angular_velocity", "axis": "x", "unit": "deg_per_sec"},
            {"name": "gy", "kind": "angular_velocity", "axis": "y", "unit": "deg_per_sec"},
            {"name": "gz", "kind": "angular_velocity", "axis": "z", "unit": "deg_per_sec"},
            {"name": "acc_norm", "kind": "derived_acceleration_norm", "unit": "g"},
        ],
    }


def create_subjects(sessions: list) -> list:
    """
    Создать subjects.json.

    Собираем уникальные subject_id из сессий.
    Известные субъекты получают заполненные поля.
    Неизвестные получают draft статус.
    """

    # Известные субъекты — заполни реальными данными позже
    known = {
        "child_01": {
            "role": "child",
            "age_group": "child",
            "dominant_hand": "right",
            "notes": "",
        },
        "child_02": {
            "role": "child",
            "age_group": "child",
            "dominant_hand": "unknown",
            "notes": "",
        },
        "adult_01": {
            "role": "adult",
            "age_group": "adult",
            "dominant_hand": "right",
            "notes": "",
        },
        "mentor_01": {
            "role": "mentor",
            "age_group": "adult",
            "dominant_hand": "right",
            "notes": "",
        },
    }

    # Собираем все subject_id из сессий
    subject_ids = set()
    for s in sessions:
        sid = s.get("subject_id")
        if sid and sid != "unknown":
            subject_ids.add(sid)

    # Добавляем известных субъектов
    subject_ids.update(known.keys())

    subjects = []
    for sid in sorted(subject_ids):
        if sid in known:
            subjects.append({"subject_id": sid, **known[sid]})
        else:
            subjects.append({
                "subject_id": sid,
                "role": "unknown",
                "age_group": "unknown",
                "dominant_hand": "unknown",
                "notes": "auto created from session data",
            })

    return subjects


def main():
    print("MotionBlocks Metadata Migration")
    print("=" * 40)

    # Проверяем что файлы существуют
    if not EXPERIMENTS_PATH.exists():
        print(f"ERROR: {EXPERIMENTS_PATH} not found")
        return

    if not SESSIONS_PATH.exists():
        print(f"ERROR: {SESSIONS_PATH} not found")
        return

    # Резервная копия
    print("\n1. Creating backup...")
    make_backup()

    # Загружаем
    print("\n2. Loading current data...")
    experiments = load_json(EXPERIMENTS_PATH)
    sessions    = load_json(SESSIONS_PATH)
    devices     = load_json(DEVICES_PATH)

    print(f"  experiments: {len(experiments)}")
    print(f"  sessions:    {len(sessions)}")
    print(f"  devices:     {len(devices)}")

    # Мигрируем
    print("\n3. Migrating...")

    new_experiments = migrate_experiments(experiments, sessions)
    new_sessions    = migrate_sessions(sessions, experiments)
    schema          = create_schema()
    subjects        = create_subjects(sessions)

    # Считаем что изменилось
    status_changed = sum(
        1 for old, new in zip(sessions, new_sessions)
        if old.get("status") != new.get("status")
    )
    print(f"  Sessions with status updated: {status_changed}")

    fields_removed = {"file_role", "mac_address", "hardware_model",
                      "records_expected", "session_id", "channels",
                      "tags", "file_id", "device_name"}
    print(f"  Fields removed from sessions: {', '.join(sorted(fields_removed))}")
    print(f"  Subjects found: {len(subjects)}")

    # Сохраняем
    print("\n4. Saving...")
    save_json(EXPERIMENTS_PATH, new_experiments)
    save_json(SESSIONS_PATH, new_sessions)
    save_json(SCHEMA_PATH, schema)

    # subjects.json создаём только если не существует
    if not SUBJECTS_PATH.exists():
        save_json(SUBJECTS_PATH, subjects)
    else:
        print(f"  Skipped (already exists): {SUBJECTS_PATH}")

    print("\nDone.")
    print()
    print("Verify the results:")
    print("  data/metadata/experiments.json")
    print("  data/metadata/recording_sessions.json")
    print("  data/metadata/schema.json       ← new")
    print("  data/metadata/subjects.json     ← new")
    print()
    print("Backup is in data/metadata/backup_*/")


if __name__ == "__main__":
    main()
