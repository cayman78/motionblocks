import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

import serial


# ============================================================
# MotionBlocks — Python Serial Logger
#
# Назначение:
# - слушать Serial-порт M5StickC Plus2;
# - читать строки протокола прошивки v0.3;
# - создавать CSV-файлы по сессиям;
# - сохранять события START / STOP и строки DATA;
# - опционально создавать черновые metadata-записи.
#
# Пример запуска:
#
# python tools/serial_logger.py --port COM6 --experiment-id EXP01 --device-id m5_001 --create-metadata
#
# Ожидаемый путь для файлов:
#
# data/raw/EXP01/m5_001/session_A001.csv
# data/raw/EXP01/m5_001/session_A002.csv
#
# Metadata:
#
# data/metadata/experiments.json
# data/metadata/recording_sessions.json
#
# Важно:
# - прошивка НЕ знает experiment_id;
# - прошивка НЕ знает device_id;
# - experiment_id и device_id задаются на стороне Python logger.
# ============================================================


CSV_HEADER = [
    "row_type",
    "session_id",
    "record_id",
    "sample_id",
    "device_timestamp_ms",
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz",
    "acc_norm",
    "event_type",
    "sample_count",
]


DEFAULT_CHANNELS = [
    {"name": "ax", "kind": "acceleration", "axis": "x", "unit": "g"},
    {"name": "ay", "kind": "acceleration", "axis": "y", "unit": "g"},
    {"name": "az", "kind": "acceleration", "axis": "z", "unit": "g"},
    {"name": "gx", "kind": "angular_velocity", "axis": "x", "unit": "deg_per_sec"},
    {"name": "gy", "kind": "angular_velocity", "axis": "y", "unit": "deg_per_sec"},
    {"name": "gz", "kind": "angular_velocity", "axis": "z", "unit": "deg_per_sec"},
    {"name": "acc_norm", "kind": "derived_acceleration_norm", "unit": "g"},
]


AUTO_STATUS = "auto created. needs description."


def now_iso() -> str:
    """Вернуть текущее локальное время без микросекунд в ISO-формате."""
    return datetime.now().replace(microsecond=0).isoformat()


def load_json_list(path: Path) -> list[dict]:
    """
    Прочитать JSON-файл, который должен содержать список объектов.

    Если файла нет или файл пустой — вернуть пустой список.
    """
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8").strip()

    if not text:
        return []

    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError(f"Metadata file must contain a JSON list: {path}")

    return data


def save_json_list(path: Path, data: list[dict]) -> None:
    """
    Сохранить список объектов в читаемом JSON-формате.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def session_number_from_id(session_id: str) -> Optional[int]:
    """
    Преобразовать A001 -> 1, A002 -> 2.

    Если формат неожиданный, вернуть None.
    """
    if len(session_id) >= 2 and session_id[0].isalpha() and session_id[1:].isdigit():
        return int(session_id[1:])

    return None


def create_draft_experiment_metadata(
    experiments_path: Path,
    experiment_id: str,
    device_id: str,
) -> None:
    """
    Добавить черновую запись в experiments.json.

    Если experiment_id уже существует — ничего не менять.
    Это важно: logger не должен перезаписывать ручные правки.
    """
    experiments = load_json_list(experiments_path)

    for item in experiments:
        if item.get("experiment_id") == experiment_id:
            print(f"[METADATA] Existing experiment preserved: {experiment_id}")
            return

    draft = {
        "experiment_id": experiment_id,
        "short_name": "unknown",
        "title": "unknown",
        "started_at": now_iso(),
        "ended_at": None,
        "location": "unknown",
        "environment": "unknown",
        "goal": "",
        "participants": [],
        "operator_id": "unknown",
        "device_ids": [device_id],
        "default_device_position": "unknown",
        "default_wrist": None,
        "default_sample_rate_hz": 10,
        "protocol": "Button-controlled recording. Button A starts/stops records. Button B switches to next session.",
        "comments": "",
        "status": AUTO_STATUS,
        "tags": [],
    }

    experiments.append(draft)
    save_json_list(experiments_path, experiments)

    print(f"[METADATA] Draft experiment created: {experiment_id}")
    print(f"[METADATA] File: {experiments_path}")


def create_draft_session_metadata(
    sessions_path: Path,
    experiment_id: str,
    device_id: str,
    session_id: str,
    file_path: Path,
) -> None:
    """
    Добавить черновую запись в recording_sessions.json.

    Если session_uid уже существует — ничего не менять.
    Это важно: logger не должен перезаписывать ручные правки.
    """
    sessions = load_json_list(sessions_path)

    session_uid = f"{experiment_id}_{device_id}_{session_id}"

    for item in sessions:
        if item.get("session_uid") == session_uid:
            print(f"[METADATA] Existing session preserved: {session_uid}")
            return

    file_id = session_number_from_id(session_id)

    draft = {
        "experiment_id": experiment_id,
        "device_id": device_id,
        "session_id": session_id,
        "session_uid": session_uid,
        "file_id": file_id,
        "file_name": file_path.name,
        "file_path": file_path.as_posix(),
        "file_role": "raw_data",
        "data_format": "wide_csv",
        "schema_version": "motionblocks.sample.v0.1",
        "movement_type": "unknown",
        "movement_label": "unknown",
        "subject_id": "unknown",
        "started_at": now_iso(),
        "sample_rate_hz": 10,
        "records_expected": None,
        "records_actual": None,
        "channels": DEFAULT_CHANNELS,
        "comment": "",
        "status": AUTO_STATUS,
        "tags": [],
    }

    sessions.append(draft)
    save_json_list(sessions_path, sessions)

    print(f"[METADATA] Draft session created: {session_uid}")
    print(f"[METADATA] File: {sessions_path}")


class SessionWriter:
    """
    Класс, отвечающий за запись данных в CSV-файлы.

    Один объект SessionWriter знает:
    - базовую папку для raw data;
    - experiment_id;
    - device_id;
    - текущую открытую сессию;
    - текущий открытый CSV-файл;
    - надо ли создавать metadata.
    """

    def __init__(
        self,
        base_dir: Path,
        experiment_id: str,
        device_id: str,
        create_metadata: bool,
        experiments_path: Path,
        sessions_path: Path,
    ) -> None:
        self.base_dir = base_dir
        self.experiment_id = experiment_id
        self.device_id = device_id

        self.create_metadata = create_metadata
        self.experiments_path = experiments_path
        self.sessions_path = sessions_path

        self.current_session_id: Optional[str] = None
        self.current_path: Optional[Path] = None
        self.current_file: Optional[TextIO] = None
        self.current_writer: Optional[csv.writer] = None

    def _session_path(self, session_id: str) -> Path:
        """
        Построить путь к CSV-файлу для заданной сессии.

        Пример:
            data/raw/EXP01/m5_001/session_A001.csv
        """
        return (
            self.base_dir
            / self.experiment_id
            / self.device_id
            / f"session_{session_id}.csv"
        )

    def open_session(self, session_id: str, timestamp_ms: str) -> None:
        """
        Открыть CSV-файл для новой сессии.

        Если до этого был открыт другой файл, он закрывается.
        Если файл новый, пишется CSV_HEADER.
        При включённом --create-metadata создаются черновые metadata-записи.
        """
        self.close_session()

        path = self._session_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        file_exists = path.exists() and path.stat().st_size > 0

        self.current_session_id = session_id
        self.current_path = path
        self.current_file = open(path, "a", newline="", encoding="utf-8")
        self.current_writer = csv.writer(self.current_file)

        if not file_exists:
            self.current_writer.writerow(CSV_HEADER)

        if self.create_metadata:
            create_draft_experiment_metadata(
                experiments_path=self.experiments_path,
                experiment_id=self.experiment_id,
                device_id=self.device_id,
            )

            create_draft_session_metadata(
                sessions_path=self.sessions_path,
                experiment_id=self.experiment_id,
                device_id=self.device_id,
                session_id=session_id,
                file_path=path,
            )

        self.write_event(
            session_id=session_id,
            record_id="",
            timestamp_ms=timestamp_ms,
            event_type="NEW_SESSION",
            sample_count="",
        )

        print(f"[SESSION] {session_id}")
        print(f"[FILE] {path}")

    def close_session(self) -> None:
        """
        Закрыть текущий CSV-файл, если он открыт.
        """
        if self.current_file is not None:
            self.current_file.flush()
            self.current_file.close()

        self.current_file = None
        self.current_writer = None
        self.current_path = None
        self.current_session_id = None

    def ensure_session(self, session_id: str) -> None:
        """
        Убедиться, что файл нужной сессии открыт.
        """
        if self.current_session_id != session_id:
            self.open_session(session_id=session_id, timestamp_ms="")

    def write_event(
        self,
        session_id: str,
        record_id: str,
        timestamp_ms: str,
        event_type: str,
        sample_count: str,
    ) -> None:
        """
        Записать EVENT-строку в CSV.
        """
        self.ensure_session(session_id)

        if self.current_writer is None or self.current_file is None:
            raise RuntimeError("No active session file")

        self.current_writer.writerow(
            [
                "EVENT",
                session_id,
                record_id,
                "",
                timestamp_ms,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                event_type,
                sample_count,
            ]
        )
        self.current_file.flush()

    def write_data(self, parts: list[str]) -> None:
        """
        Записать DATA-строку в CSV.

        Ожидаемый формат:
            DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm
        """
        if len(parts) != 12:
            print(f"[WARN] Bad DATA row, expected 12 fields, got {len(parts)}: {parts}")
            return

        (
            _row_type,
            session_id,
            record_id,
            sample_id,
            timestamp_ms,
            ax,
            ay,
            az,
            gx,
            gy,
            gz,
            acc_norm,
        ) = parts

        self.ensure_session(session_id)

        if self.current_writer is None or self.current_file is None:
            raise RuntimeError("No active session file")

        self.current_writer.writerow(
            [
                "DATA",
                session_id,
                record_id,
                sample_id,
                timestamp_ms,
                ax,
                ay,
                az,
                gx,
                gy,
                gz,
                acc_norm,
                "",
                "",
            ]
        )
        self.current_file.flush()


def handle_event(parts: list[str], writer: SessionWriter) -> None:
    """
    Обработать EVENT-строку от устройства.

    Возможные события:
        EVENT,NEW_SESSION,session_id,timestamp_ms
        EVENT,START,session_id,record_id,timestamp_ms
        EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
    """
    if len(parts) < 3:
        print(f"[WARN] Bad EVENT row: {parts}")
        return

    event_type = parts[1]

    if event_type == "NEW_SESSION":
        if len(parts) != 4:
            print(f"[WARN] Bad NEW_SESSION event: {parts}")
            return

        session_id = parts[2]
        timestamp_ms = parts[3]

        writer.open_session(session_id=session_id, timestamp_ms=timestamp_ms)
        return

    if event_type == "START":
        if len(parts) != 5:
            print(f"[WARN] Bad START event: {parts}")
            return

        session_id = parts[2]
        record_id = parts[3]
        timestamp_ms = parts[4]

        writer.write_event(
            session_id=session_id,
            record_id=record_id,
            timestamp_ms=timestamp_ms,
            event_type="START",
            sample_count="",
        )

        print(f"[START] session={session_id}, record={record_id}")
        return

    if event_type == "STOP":
        if len(parts) != 6:
            print(f"[WARN] Bad STOP event: {parts}")
            return

        session_id = parts[2]
        record_id = parts[3]
        timestamp_ms = parts[4]
        sample_count = parts[5]

        writer.write_event(
            session_id=session_id,
            record_id=record_id,
            timestamp_ms=timestamp_ms,
            event_type="STOP",
            sample_count=sample_count,
        )

        print(
            f"[STOP] session={session_id}, "
            f"record={record_id}, samples={sample_count}"
        )
        return

    print(f"[INFO] Ignored event type: {event_type}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MotionBlocks Serial Logger")

    parser.add_argument(
        "--port",
        default="COM6",
        help="Serial port, for example COM6",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Serial baud rate",
    )
    parser.add_argument(
        "--experiment-id",
        required=True,
        help="Experiment id, for example EXP01",
    )
    parser.add_argument(
        "--device-id",
        required=True,
        help="Device id, for example m5_001",
    )
    parser.add_argument(
        "--base-dir",
        default="data/raw",
        help="Base directory for raw data",
    )
    parser.add_argument(
        "--create-metadata",
        action="store_true",
        help="Create draft records in metadata JSON files",
    )
    parser.add_argument(
        "--experiments-path",
        default="data/metadata/experiments.json",
        help="Path to experiments metadata JSON file",
    )
    parser.add_argument(
        "--sessions-path",
        default="data/metadata/recording_sessions.json",
        help="Path to recording sessions metadata JSON file",
    )

    args = parser.parse_args()

    writer = SessionWriter(
        base_dir=Path(args.base_dir),
        experiment_id=args.experiment_id,
        device_id=args.device_id,
        create_metadata=args.create_metadata,
        experiments_path=Path(args.experiments_path),
        sessions_path=Path(args.sessions_path),
    )

    print("MotionBlocks Serial Logger")
    print(f"Port:            {args.port}")
    print(f"Baud:            {args.baud}")
    print(f"Experiment id:   {args.experiment_id}")
    print(f"Device id:       {args.device_id}")
    print(f"Base dir:        {args.base_dir}")
    print(f"Create metadata: {args.create_metadata}")
    print(f"Experiments:     {args.experiments_path}")
    print(f"Sessions:        {args.sessions_path}")
    print("Waiting for device data...")
    print("Press Ctrl+C to stop.")
    print()

    try:
        with serial.Serial(args.port, args.baud, timeout=1) as ser:
            while True:
                raw_line = ser.readline()

                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="ignore").strip()

                if not line:
                    continue

                print(line)

                parts = line.split(",")

                if not parts:
                    continue

                if parts[0] == "EVENT":
                    handle_event(parts, writer)
                    continue

                if parts[0] == "DATA":
                    writer.write_data(parts)
                    continue

                # Стартовые информационные строки прошивки игнорируем.
                print(f"[INFO] Ignored line: {line}")

    except KeyboardInterrupt:
        print()
        print("Stopping logger...")

    finally:
        writer.close_session()
        print("Logger stopped.")


if __name__ == "__main__":
    main()
