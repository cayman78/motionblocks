import argparse  # нужна для чтения параметров командной строки: --host, --port, --experiment-id, --device-id
import csv  # нужна для записи EVENT/DATA строк в CSV-файлы сессий
import json  # нужна для чтения и записи metadata-файлов experiments.json и recording_sessions.json
import re  # нужна для поиска run_id в именах существующих файлов
import threading  # нужна для Lock — защиты от одновременной записи в нескольких потоках
from datetime import datetime  # нужна для создания timestamp в metadata, например started_at
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # нужны для создания простого HTTP-сервера и обработки GET/POST запросов
from pathlib import Path  # нужна для удобной и безопасной работы с путями к файлам и папкам
from typing import Optional, TextIO  # нужны для type hints: необязательные значения и тип открытого текстового файла
from urllib.parse import urlparse  # нужна для разбора пути HTTP-запроса, например /health или /line

# ============================================================
# MotionBlocks — HTTP Logger
#
# Назначение:
# - поднять локальный HTTP-сервер на ноутбуке;
# - принимать строки протокола от M5StickC Plus2 по Wi-Fi;
# - принимать как одиночные строки, так и batch из нескольких строк;
# - сохранять эти строки в CSV-файлы;
# - опционально создавать черновые записи metadata.
#
# Общая схема:
#
#   M5StickC Plus2
#       → Wi-Fi
#       → HTTP POST /line
#       → tools/http_logger.py
#       → data/raw/EXP01/m5_001/run_A_session_A001_100Hz.csv
#       → data/metadata/experiments.json
#       → data/metadata/recording_sessions.json
#
# Важно:
# - формат строк EVENT / DATA не меняется;
# - HTTP — это только транспорт;
# - firmware может отправлять одну строку на POST;
# - firmware может отправлять несколько DATA-строк в одном POST body;
# - logger разбивает HTTP body через splitlines() и обрабатывает
#   каждую строку как обычную строку протокола.
#
# recording_run_id:
# - назначается logger'ом при старте, не firmware'ом;
# - это одна заглавная буква: A, B, C, ...;
# - определяется сканированием папки data/raw/EXP/device/ при старте;
# - если там нет файлов run_*_session_*.csv, первый run = A;
# - если максимальный run = B, следующий = C;
# - старые файлы session_A001.csv (без run_id) не мешают сканированию;
# - один run_id живёт на весь запуск logger'а;
# - после device reset и нового запуска logger'а run_id станет следующей буквой.
#
# Имя файла:
#
#   run_A_session_A001_100Hz.csv
#   run_A_session_A002_100Hz.csv
#   run_B_session_A001_50Hz.csv
#
# Текущая transport-модель:
#
#   IDLE / service events:
#       DEVICE_INFO
#       SAMPLE_RATE
#       NEW_SESSION
#       обычно приходят как отдельные one-shot HTTP POST.
#
#   RECORDING / data stream:
#       START приходит сразу;
#       DATA может приходить пачками, например 25 строк в одном POST;
#       перед STOP прошивка должна сбросить накопленный DATA batch;
#       STOP приходит после всех DATA текущей записи.
#
# Пример запуска:
#
#   python tools/http_logger.py --host 0.0.0.0 --port 8080 --experiment-id EXP01 --device-id m5_001 --create-metadata
#
# Проверка:
#
#   GET  http://127.0.0.1:8080/health
#   POST http://127.0.0.1:8080/line
#
# ============================================================


# ------------------------------------------------------------
# Заголовок CSV-файла.
#
# В один файл пишем и события, и данные.
#
# row_type:
#   EVENT — служебная строка: NEW_SESSION / START / STOP и т.п.
#   DATA  — строка с измерением IMU
#
# Batch mode не меняет CSV schema:
# несколько DATA-строк могут прийти в одном HTTP POST,
# но в CSV они всё равно записываются как отдельные строки.
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Описание каналов текущей схемы данных.
# ------------------------------------------------------------
DEFAULT_CHANNELS = [
    {"name": "ax", "kind": "acceleration", "axis": "x", "unit": "g"},
    {"name": "ay", "kind": "acceleration", "axis": "y", "unit": "g"},
    {"name": "az", "kind": "acceleration", "axis": "z", "unit": "g"},
    {"name": "gx", "kind": "angular_velocity", "axis": "x", "unit": "deg_per_sec"},
    {"name": "gy", "kind": "angular_velocity", "axis": "y", "unit": "deg_per_sec"},
    {"name": "gz", "kind": "angular_velocity", "axis": "z", "unit": "deg_per_sec"},
    {"name": "acc_norm", "kind": "derived_acceleration_norm", "unit": "g"},
]


# Статус для metadata-записей, созданных автоматически.
AUTO_STATUS = "auto created. needs description."

# Паттерн для поиска run_id в именах файлов.
# Пример: run_A_session_A001_100Hz.csv → группа 1 = "A"
RUN_FILE_PATTERN = re.compile(r"^run_([A-Z]+)_session_.*\.csv$")


def now_iso() -> str:
    """
    Вернуть текущее локальное время в ISO-формате без микросекунд.

        2026-06-10T19:30:00
    """
    return datetime.now().replace(microsecond=0).isoformat()


def load_json_list(path: Path) -> list[dict]:
    """
    Прочитать JSON-файл, который должен содержать список объектов.

    Если файла нет или он пустой — возвращаем пустой список.
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
    Преобразовать session_id в числовой file_id.

        A001 -> 1
        A015 -> 15
    """
    if len(session_id) >= 2 and session_id[0].isalpha() and session_id[1:].isdigit():
        return int(session_id[1:])

    return None


def normalize_mac_address(mac_address: str) -> str:
    """
    Нормализовать MAC-адрес для сопоставления.

        f0:24:f9:97:ed:08 -> F0:24:F9:97:ED:08
    """
    return mac_address.strip().upper()


def find_device_by_mac(devices: list[dict], mac_address: str) -> Optional[dict]:
    """
    Найти устройство в registry по MAC-адресу.
    """
    target_mac = normalize_mac_address(mac_address)

    for device in devices:
        current_mac = device.get("mac_address")

        if not current_mac:
            continue

        if normalize_mac_address(str(current_mac)) == target_mac:
            return device

    return None


# ------------------------------------------------------------
# recording_run_id
#
# run_id — это одна или несколько заглавных букв: A, B, C, ... Z, AA, AB, ...
# Аналогично именованию колонок в Excel.
#
# Логика:
# - при старте logger сканирует папку data/raw/EXP/device/;
# - ищет файлы по паттерну run_*_session_*.csv;
# - находит максимальный run_id среди существующих файлов;
# - следующий run_id = следующая буква после максимального.
#
# Примеры:
#   нет файлов run_*  →  A
#   max = A           →  B
#   max = Z           →  AA
#   max = AZ          →  BA
# ------------------------------------------------------------

def run_id_to_int(run_id: str) -> int:
    """
    Перевести буквенный run_id в число для сравнения.

        A  -> 1
        B  -> 2
        Z  -> 26
        AA -> 27
        AB -> 28
    """
    result = 0
    for ch in run_id:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


def int_to_run_id(n: int) -> str:
    """
    Перевести число обратно в буквенный run_id.

        1  -> A
        26 -> Z
        27 -> AA
    """
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(ord('A') + remainder) + result
    return result


def find_next_run_id(device_dir: Path) -> str:
    """
    Найти следующий свободный recording_run_id для данной папки устройства.

    Сканируем файлы вида:

        run_A_session_A001_100Hz.csv
        run_B_session_A001_50Hz.csv

    Берём максимальный существующий run_id и возвращаем следующий.

    Старые файлы session_A001.csv (без run_id) игнорируются.

    Если подходящих файлов нет — возвращаем "A".
    """
    if not device_dir.exists():
        return "A"

    max_n = 0

    for f in device_dir.iterdir():
        if not f.is_file():
            continue

        m = RUN_FILE_PATTERN.match(f.name)

        if not m:
            continue

        run_id = m.group(1)
        n = run_id_to_int(run_id)

        if n > max_n:
            max_n = n

    return int_to_run_id(max_n + 1)


def create_draft_experiment_metadata(
    experiments_path: Path,
    experiment_id: str,
    device_id: str,
) -> None:
    """
    Добавить черновую запись об эксперименте в experiments.json.

    Если experiment_id уже есть — не перезаписываем.
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
    recording_run_id: str,
    file_path: Path,
    mac_address: Optional[str] = None,
    firmware_version: Optional[str] = None,
    device_registry_record: Optional[dict] = None,
    sample_rate_hz: int = 10,
) -> None:
    """
    Добавить черновую запись о recording session в recording_sessions.json.

    session_uid теперь включает recording_run_id:

        EXP01_m5_001_A_A001

    Если session_uid уже есть — не перезаписываем.
    """
    sessions = load_json_list(sessions_path)

    # session_uid включает recording_run_id для уникальности.
    session_uid = f"{experiment_id}_{device_id}_{recording_run_id}_{session_id}"

    for item in sessions:
        if item.get("session_uid") == session_uid:
            print(f"[METADATA] Existing session preserved: {session_uid}")
            return

    file_id = session_number_from_id(session_id)

    draft = {
        "experiment_id": experiment_id,
        "device_id": device_id,
        "recording_run_id": recording_run_id,
        "device_session_id": session_id,
        # session_id сохраняем для обратной совместимости
        "session_id": session_id,
        "session_uid": session_uid,
        "file_id": file_id,
        "file_name": file_path.name,
        "file_path": file_path.as_posix(),
        "file_role": "raw_data",
        "data_format": "wide_csv",
        "schema_version": "motionblocks.sample.v0.1",
        "mac_address": mac_address,
        "firmware_version": firmware_version,
        "device_name": device_registry_record.get("device_name") if device_registry_record else None,
        "hardware_model": device_registry_record.get("hardware_model") if device_registry_record else None,
        "movement_type": "unknown",
        "movement_label": "unknown",
        "subject_id": "unknown",
        "started_at": now_iso(),
        "sample_rate_hz": sample_rate_hz,
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
    Класс, который пишет строки протокола MotionBlocks в CSV-файлы.

    Он не знает ничего про HTTP.
    HTTP-сервер отвечает за транспорт.
    SessionWriter отвечает за запись данных.

    Thread safety:
    Защищён через self._lock.
    ThreadingHTTPServer создаёт отдельный поток на каждый запрос,
    поэтому при высокой частоте дискретизации несколько потоков могут
    одновременно вызывать write_data().
    """

    def __init__(
        self,
        base_dir: Path,
        experiment_id: str,
        device_id: Optional[str],
        create_metadata: bool,
        experiments_path: Path,
        sessions_path: Path,
        devices_path: Path,
    ) -> None:
        self.base_dir = base_dir
        self.experiment_id = experiment_id
        self.cli_device_id = device_id
        self.effective_device_id: Optional[str] = device_id

        self.devices_path = devices_path
        self.devices = load_json_list(devices_path)
        self.device_registry_record: Optional[dict] = None

        self.mac_address: Optional[str] = None
        self.firmware_version: Optional[str] = None

        # Частота дискретизации, выбранная на устройстве.
        # Обновляется при получении EVENT,SAMPLE_RATE.
        self.sample_rate_hz: int = 10

        self.create_metadata = create_metadata
        self.experiments_path = experiments_path
        self.sessions_path = sessions_path

        # recording_run_id назначается при первом открытии сессии,
        # когда уже известен effective_device_id.
        # До этого момента None.
        self.recording_run_id: Optional[str] = None

        self.current_session_id: Optional[str] = None
        self.current_path: Optional[Path] = None
        self.current_file: Optional[TextIO] = None
        self.current_writer: Optional[csv.writer] = None

        # Lock для thread-safe записи в файл.
        self._lock = threading.Lock()

    def require_device_id(self) -> str:
        """
        Вернуть эффективный device_id.

        Если device_id неизвестен — открывать session-файл нельзя.
        """
        if self.effective_device_id:
            return self.effective_device_id

        raise RuntimeError(
            "device_id is not provided and device could not be resolved from DEVICE_INFO. "
            "Provide --device-id or register device MAC in data/metadata/devices.json."
        )

    def _ensure_recording_run_id(self) -> str:
        """
        Убедиться, что recording_run_id назначен.

        Если ещё не назначен — сканируем папку устройства и назначаем.

        Это делается лениво, потому что при старте logger'а
        effective_device_id может ещё не быть известен
        (если --device-id не задан и DEVICE_INFO ещё не пришёл).
        """
        if self.recording_run_id is not None:
            return self.recording_run_id

        device_id = self.require_device_id()
        device_dir = self.base_dir / self.experiment_id / device_id

        self.recording_run_id = find_next_run_id(device_dir)

        print(f"[RUN] recording_run_id assigned: {self.recording_run_id}")
        print(f"[RUN] scanned: {device_dir}")

        return self.recording_run_id

    def handle_device_info(
        self,
        mac_address: str,
        firmware_version: str,
        timestamp_ms: str,
    ) -> None:
        """
        Обработать EVENT,DEVICE_INFO.

        Правило:
        - если --device-id задан, он имеет приоритет;
        - если --device-id не задан, device_id ищется в devices.json по MAC.
        """
        self.mac_address = normalize_mac_address(mac_address)
        self.firmware_version = firmware_version

        registry_record = find_device_by_mac(self.devices, self.mac_address)
        self.device_registry_record = registry_record

        if self.cli_device_id:
            if registry_record is None:
                print(
                    f"WARNING: DEVICE_INFO MAC {self.mac_address} is not registered in {self.devices_path}."
                )
                print(f"Using explicit --device-id {self.cli_device_id}.")
                return

            registry_device_id = registry_record.get("device_id")

            if registry_device_id == self.cli_device_id:
                print(
                    f"DEVICE OK: --device-id {self.cli_device_id} matches DEVICE_INFO MAC {self.mac_address}."
                )
                return

            print(
                f"WARNING: --device-id is {self.cli_device_id}, "
                f"but DEVICE_INFO MAC {self.mac_address} is registered as {registry_device_id}."
            )
            print(f"Using explicit --device-id {self.cli_device_id}.")
            return

        if registry_record is None:
            raise RuntimeError(
                f"device_id is not provided and DEVICE_INFO MAC {self.mac_address} "
                f"is not registered in {self.devices_path}. "
                "Provide --device-id or register the device MAC."
            )

        registry_device_id = registry_record.get("device_id")

        if not registry_device_id:
            raise RuntimeError(
                f"Device registry record for MAC {self.mac_address} has no device_id."
            )

        self.effective_device_id = str(registry_device_id)

        print(
            f"DEVICE OK: resolved device_id {self.effective_device_id} "
            f"from DEVICE_INFO MAC {self.mac_address}."
        )

    def handle_sample_rate(self, sample_rate_hz: str, timestamp_ms: str) -> None:
        """
        Обработать EVENT,SAMPLE_RATE.

        Значение сохраняется и используется при создании draft metadata
        и при формировании имени файла.
        """
        try:
            parsed_rate = int(sample_rate_hz)
        except ValueError:
            print(f"[WARN] Bad SAMPLE_RATE value: {sample_rate_hz}")
            return

        if parsed_rate <= 0:
            print(f"[WARN] Bad SAMPLE_RATE value: {sample_rate_hz}")
            return

        self.sample_rate_hz = parsed_rate

        print(
            f"[CONFIG] sample_rate_hz={self.sample_rate_hz} "
            f"(device timestamp {timestamp_ms})"
        )

    def _session_path(self, session_id: str) -> Path:
        """
        Построить путь к CSV-файлу сессии.

        Новый формат:

            data/raw/EXP01/m5_001/run_A_session_A001_100Hz.csv

        Пример:

            base_dir          = data/raw
            experiment_id     = EXP01
            device_id         = m5_001
            recording_run_id  = A
            session_id        = A001
            sample_rate_hz    = 100

        Результат:

            data/raw/EXP01/m5_001/run_A_session_A001_100Hz.csv
        """
        run_id = self._ensure_recording_run_id()
        device_id = self.require_device_id()
        file_name = f"run_{run_id}_session_{session_id}_{self.sample_rate_hz}Hz.csv"

        return (
            self.base_dir
            / self.experiment_id
            / device_id
            / file_name
        )

    def open_session(self, session_id: str, timestamp_ms: str) -> None:
        """
        Открыть CSV-файл для заданной сессии.

        Если был открыт другой файл, он закрывается.

        Новый файл — всегда новый: режим "w", не "a".
        Это безопасно, потому что имя файла уже включает run_id.
        Если файл с таким именем вдруг уже есть (нештатная ситуация),
        мы печатаем предупреждение.
        """
        with self._lock:
            self._close_session_unsafe()

            path = self._session_path(session_id)
            path.parent.mkdir(parents=True, exist_ok=True)

            if path.exists():
                print(
                    f"[WARN] File already exists, will append: {path}"
                )
                mode = "a"
                write_header = False
            else:
                mode = "w"
                write_header = True

            self.current_session_id = session_id
            self.current_path = path
            self.current_file = open(path, mode, newline="", encoding="utf-8")
            self.current_writer = csv.writer(self.current_file)

            if write_header:
                self.current_writer.writerow(CSV_HEADER)

            if self.create_metadata:
                run_id = self._ensure_recording_run_id()

                create_draft_experiment_metadata(
                    experiments_path=self.experiments_path,
                    experiment_id=self.experiment_id,
                    device_id=self.require_device_id(),
                )

                create_draft_session_metadata(
                    sessions_path=self.sessions_path,
                    experiment_id=self.experiment_id,
                    device_id=self.require_device_id(),
                    session_id=session_id,
                    recording_run_id=run_id,
                    file_path=path,
                    mac_address=self.mac_address,
                    firmware_version=self.firmware_version,
                    device_registry_record=self.device_registry_record,
                    sample_rate_hz=self.sample_rate_hz,
                )

            self._write_event_unsafe(
                session_id=session_id,
                record_id="",
                timestamp_ms=timestamp_ms,
                event_type="NEW_SESSION",
                sample_count="",
            )

        print(f"[SESSION] {session_id}")
        print(f"[RUN] {self.recording_run_id}")
        print(f"[FILE] {path}")

    def _close_session_unsafe(self) -> None:
        """
        Закрыть текущий CSV-файл без захвата lock.

        Вызывается только изнутри методов, которые уже держат lock,
        или из close_session() при завершении программы.
        """
        if self.current_file is not None:
            self.current_file.flush()
            self.current_file.close()

        self.current_file = None
        self.current_writer = None
        self.current_path = None
        self.current_session_id = None

    def close_session(self) -> None:
        """
        Закрыть текущий CSV-файл.

        Вызывается при завершении программы (Ctrl+C).
        """
        with self._lock:
            self._close_session_unsafe()

    def ensure_session(self, session_id: str) -> None:
        """
        Убедиться, что открыт файл нужной сессии.

        Если пришла строка A002, а открыт файл A001,
        logger переключится на файл A002.

        Вызывается без lock — lock захватывается внутри open_session.
        """
        if self.current_session_id != session_id:
            if self.current_session_id is not None:
                print(f"[SESSION] switching from {self.current_session_id} to {session_id}")
            self.open_session(session_id=session_id, timestamp_ms="")

    def _write_event_unsafe(
        self,
        session_id: str,
        record_id: str,
        timestamp_ms: str,
        event_type: str,
        sample_count: str,
    ) -> None:
        """
        Записать EVENT-строку в CSV без захвата lock.

        Вызывается только изнутри методов, которые уже держат lock.
        """
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

    def write_event(
        self,
        session_id: str,
        record_id: str,
        timestamp_ms: str,
        event_type: str,
        sample_count: str,
    ) -> None:
        """
        Записать EVENT-строку в CSV (публичный метод с lock).
        """
        self.ensure_session(session_id)

        with self._lock:
            self._write_event_unsafe(
                session_id=session_id,
                record_id=record_id,
                timestamp_ms=timestamp_ms,
                event_type=event_type,
                sample_count=sample_count,
            )

    def write_data(self, parts: list[str]) -> None:
        """
        Записать DATA-строку в CSV.

        Ожидаемый формат:

            DATA,session_id,record_id,sample_id,timestamp_ms,ax,ay,az,gx,gy,gz,acc_norm

        После split(",") должно быть 12 полей.
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

        with self._lock:
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
    Обработать EVENT-строку.

    Возможные события:

        EVENT,DEVICE_INFO,mac_address,firmware_version,timestamp_ms
        EVENT,SAMPLE_RATE,sample_rate_hz,timestamp_ms
        EVENT,NEW_SESSION,session_id,timestamp_ms
        EVENT,START,session_id,record_id,timestamp_ms
        EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
        EVENT,IMU_NOT_UPDATED,session_id,record_id,timestamp_ms
    """
    if len(parts) < 3:
        print(f"[WARN] Bad EVENT row: {parts}")
        return

    event_type = parts[1]

    if event_type == "DEVICE_INFO":
        if len(parts) != 5:
            print(f"[WARN] Bad DEVICE_INFO event: {parts}")
            return

        writer.handle_device_info(
            mac_address=parts[2],
            firmware_version=parts[3],
            timestamp_ms=parts[4],
        )

        print("[INFO] Received event type: DEVICE_INFO")
        return

    if event_type == "SAMPLE_RATE":
        if len(parts) != 4:
            print(f"[WARN] Bad SAMPLE_RATE event: {parts}")
            return

        writer.handle_sample_rate(
            sample_rate_hz=parts[2],
            timestamp_ms=parts[3],
        )
        return

    if event_type == "NEW_SESSION":
        if len(parts) != 4:
            print(f"[WARN] Bad NEW_SESSION event: {parts}")
            return

        writer.open_session(session_id=parts[2], timestamp_ms=parts[3])
        return

    if event_type == "START":
        if len(parts) != 5:
            print(f"[WARN] Bad START event: {parts}")
            return

        writer.write_event(
            session_id=parts[2],
            record_id=parts[3],
            timestamp_ms=parts[4],
            event_type="START",
            sample_count="",
        )

        print(f"[START] session={parts[2]}, record={parts[3]}")
        return

    if event_type == "STOP":
        if len(parts) != 6:
            print(f"[WARN] Bad STOP event: {parts}")
            return

        writer.write_event(
            session_id=parts[2],
            record_id=parts[3],
            timestamp_ms=parts[4],
            event_type="STOP",
            sample_count=parts[5],
        )

        print(
            f"[STOP] session={parts[2]}, "
            f"record={parts[3]}, samples={parts[5]}"
        )
        return

    if event_type == "IMU_NOT_UPDATED":
        # Firmware шлёт это событие если IMU не вернул данные.
        # Записываем в CSV для последующего анализа качества данных.
        if len(parts) == 5:
            writer.write_event(
                session_id=parts[2],
                record_id=parts[3],
                timestamp_ms=parts[4],
                event_type="IMU_NOT_UPDATED",
                sample_count="",
            )
        print(f"[WARN] IMU_NOT_UPDATED: session={parts[2] if len(parts) > 2 else '?'}")
        return

    print(f"[INFO] Ignored event type: {event_type}")


def handle_protocol_line(line: str, writer: SessionWriter) -> None:
    """
    Обработать одну строку протокола MotionBlocks.

    Примеры строк:

        EVENT,DEVICE_INFO,F0:24:F9:97:ED:08,motionblocks.logger.v0.6,6972
        EVENT,SAMPLE_RATE,50,7200
        EVENT,NEW_SESSION,A001,7425
        EVENT,START,A001,1,13000
        DATA,A001,1,1,13100,0.01,-0.03,0.98,0.1,0.0,0.0,0.98
        EVENT,STOP,A001,1,19000,60
    """
    line = line.strip()

    if not line:
        return

    print(line)

    parts = line.split(",")

    if not parts:
        return

    if parts[0] == "EVENT":
        handle_event(parts, writer)
        return

    if parts[0] == "DATA":
        writer.write_data(parts)
        return

    print(f"[INFO] Ignored line: {line}")


class MotionBlocksRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler.

    Поддерживаем два endpoint:

        GET /health   — проверка, что сервер жив
        POST /line    — основной endpoint для строк протокола
    """

    writer: SessionWriter

    def log_message(self, format: str, *args) -> None:
        """
        Отключить стандартный HTTP-log.

        При 100 Hz стандартный лог быстро засорит консоль.
        """
        return

    def _send_text_response(self, status_code: int, text: str) -> None:
        body = text.encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_text_response(200, "ok\n")
            return

        self._send_text_response(404, "not found\n")

    def do_POST(self) -> None:
        """
        Обработка POST /line.

        Body может содержать одну строку или batch из нескольких строк.
        splitlines() делает batch прозрачным для остальной логики.
        """
        parsed = urlparse(self.path)

        if parsed.path != "/line":
            self._send_text_response(404, "not found\n")
            return

        content_length_header = self.headers.get("Content-Length")

        if content_length_header is None:
            self._send_text_response(411, "missing content length\n")
            return

        try:
            content_length = int(content_length_header)
        except ValueError:
            self._send_text_response(400, "bad content length\n")
            return

        raw_body = self.rfile.read(content_length)
        body = raw_body.decode("utf-8", errors="ignore").strip()

        if not body:
            self._send_text_response(400, "empty body\n")
            return

        try:
            for line in body.splitlines():
                line = line.strip()

                if not line:
                    continue

                handle_protocol_line(line, self.writer)

        except Exception as exc:
            print(f"[ERROR] Failed to handle request: {exc}")
            self._send_text_response(500, f"error: {exc}\n")
            return

        self._send_text_response(200, "ok\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="MotionBlocks HTTP Logger")

    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--device-id", required=False, default=None)
    parser.add_argument("--base-dir", default="data/raw")
    parser.add_argument("--create-metadata", action="store_true")
    parser.add_argument("--experiments-path", default="data/metadata/experiments.json")
    parser.add_argument("--sessions-path", default="data/metadata/recording_sessions.json")
    parser.add_argument("--devices-path", default="data/metadata/devices.json")

    args = parser.parse_args()

    writer = SessionWriter(
        base_dir=Path(args.base_dir),
        experiment_id=args.experiment_id,
        device_id=args.device_id,
        create_metadata=args.create_metadata,
        experiments_path=Path(args.experiments_path),
        sessions_path=Path(args.sessions_path),
        devices_path=Path(args.devices_path),
    )

    MotionBlocksRequestHandler.writer = writer

    server = ThreadingHTTPServer(
        (args.host, args.port),
        MotionBlocksRequestHandler,
    )

    print("MotionBlocks HTTP Logger")
    print(f"Host:            {args.host}")
    print(f"Port:            {args.port}")
    print(f"Experiment id:   {args.experiment_id}")
    print(f"Device id:       {args.device_id if args.device_id else '(auto from DEVICE_INFO)'}")
    print(f"Devices:         {args.devices_path}")
    print("Sample rate:     auto from EVENT,SAMPLE_RATE, default 10 Hz")
    print("HTTP body:       one protocol line or newline-separated batch")
    print(f"Base dir:        {args.base_dir}")
    print(f"Create metadata: {args.create_metadata}")
    print(f"Experiments:     {args.experiments_path}")
    print(f"Sessions:        {args.sessions_path}")
    print()
    print("recording_run_id will be assigned on first session open.")
    print()
    print("Endpoints:")
    print(f"  GET  http://{args.host}:{args.port}/health")
    print(f"  POST http://{args.host}:{args.port}/line")
    print()
    print("For local test use:")
    print(f"  http://127.0.0.1:{args.port}/health")
    print()
    print("Waiting for device data...")
    print("Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("Stopping HTTP logger...")

    finally:
        server.server_close()
        writer.close_session()
        print("HTTP logger stopped.")


if __name__ == "__main__":
    main()
