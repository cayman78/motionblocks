import argparse  # нужна для чтения параметров командной строки: --host, --port, --experiment-id, --device-id
import csv  # нужна для записи EVENT/DATA строк в CSV-файлы сессий
import json  # нужна для чтения и записи metadata-файлов experiments.json и recording_sessions.json
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
# - сохранять эти строки в те же CSV-файлы, что и serial_logger.py;
# - опционально создавать черновые записи metadata.
#
# Общая схема:
#
#   M5StickC Plus2
#       → Wi-Fi
#       → HTTP POST /line
#       → tools/http_logger.py
#       → data/raw/EXP01/m5_001/session_A001.csv
#       → data/metadata/experiments.json
#       → data/metadata/recording_sessions.json
#
# Важно:
# - формат строк EVENT / DATA не меняется;
# - меняется только транспорт: вместо Serial используется HTTP;
# - это позволит надеть устройство на руку и писать данные без провода.
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
# Пример body для POST /line:
#
#   EVENT,NEW_SESSION,A001,12345
#
# ============================================================


# ------------------------------------------------------------
# Заголовок CSV-файла.
#
# В один файл пишем и события, и данные.
#
# row_type:
#   EVENT — служебная строка: NEW_SESSION / START / STOP
#   DATA  — строка с измерением IMU
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
#
# Эти данные попадают в черновую metadata-запись по сессии.
# Сейчас схема простая:
# - 3 оси акселерометра;
# - 3 оси гироскопа;
# - производный показатель acc_norm.
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
# Смысл: структура создана, но человек должен позже заполнить описание.
AUTO_STATUS = "auto created. needs description."


def now_iso() -> str:
    """
    Вернуть текущее локальное время в ISO-формате.

    Микросекунды убираем, чтобы timestamp был читаемым:

        2026-06-10T19:30:00

    а не:

        2026-06-10T19:30:00.123456
    """
    return datetime.now().replace(microsecond=0).isoformat()


def load_json_list(path: Path) -> list[dict]:
    """
    Прочитать JSON-файл, который должен содержать список объектов.

    Пример ожидаемого содержимого:

        [
          {"experiment_id": "EXP01"},
          {"experiment_id": "EXP02"}
        ]

    Если файла нет — возвращаем пустой список.
    Если файл пустой — тоже возвращаем пустой список.

    Это удобно: logger может сам создать metadata-файлы при первом запуске.
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

    indent=2 делает файл удобным для ручного просмотра и редактирования.
    ensure_ascii=False позволяет нормально сохранять русский текст.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def session_number_from_id(session_id: str) -> Optional[int]:
    """
    Преобразовать session_id в числовой file_id.

    Пример:

        A001 -> 1
        A002 -> 2
        A015 -> 15

    Если формат неожиданный, возвращаем None.
    """
    if len(session_id) >= 2 and session_id[0].isalpha() and session_id[1:].isdigit():
        return int(session_id[1:])

    return None


def normalize_mac_address(mac_address: str) -> str:
    """
    Нормализовать MAC-адрес для сопоставления.

    Пример:

        f0:24:f9:97:ed:08 -> F0:24:F9:97:ED:08
    """
    return mac_address.strip().upper()


def find_device_by_mac(devices: list[dict], mac_address: str) -> Optional[dict]:
    """
    Найти устройство в registry по MAC-адресу.

    devices.json ожидается в формате:

        [
          {
            "device_id": "m5_001",
            "mac_address": "F0:24:F9:97:ED:08"
          }
        ]
    """
    target_mac = normalize_mac_address(mac_address)

    for device in devices:
        current_mac = device.get("mac_address")

        if not current_mac:
            continue

        if normalize_mac_address(str(current_mac)) == target_mac:
            return device

    return None


def create_draft_experiment_metadata(
    experiments_path: Path,
    experiment_id: str,
    device_id: str,
) -> None:
    """
    Добавить черновую запись об эксперименте в experiments.json.

    Важное правило:
    если experiment_id уже есть, ничего не перезаписываем.

    Почему:
    человек мог уже руками заполнить title, goal, participants, comments.
    Logger не должен уничтожать ручные правки.
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
    mac_address: Optional[str] = None,
    firmware_version: Optional[str] = None,
    device_registry_record: Optional[dict] = None,
) -> None:
    """
    Добавить черновую запись о recording session в recording_sessions.json.

    session_uid строится так:

        EXP01_m5_001_A001

    Важное правило:
    если session_uid уже есть, ничего не перезаписываем.
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
        "mac_address": mac_address,
        "firmware_version": firmware_version,
        "device_name": device_registry_record.get("device_name") if device_registry_record else None,
        "hardware_model": device_registry_record.get("hardware_model") if device_registry_record else None,
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
    Класс, который пишет строки протокола MotionBlocks в CSV-файлы.

    Он не знает ничего про HTTP.
    Его задача ниже уровнем:

        протокольная строка EVENT/DATA
            → CSV-файл нужной сессии
            → metadata при необходимости

    Это важно архитектурно:
    HTTP-сервер отвечает за транспорт.
    SessionWriter отвечает за запись данных.
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
        # Базовая папка для raw data, обычно data/raw.
        self.base_dir = base_dir

        # experiment_id задаётся пользователем при запуске logger.
        # device_id может быть задан явно через --device-id
        # или автоматически определён по DEVICE_INFO / devices.json.
        self.experiment_id = experiment_id
        self.cli_device_id = device_id
        self.effective_device_id: Optional[str] = device_id

        # Пути и registry устройств.
        self.devices_path = devices_path
        self.devices = load_json_list(devices_path)
        self.device_registry_record: Optional[dict] = None

        # DEVICE_INFO, полученный от устройства.
        self.mac_address: Optional[str] = None
        self.firmware_version: Optional[str] = None

        # Надо ли автоматически создавать черновую metadata.
        self.create_metadata = create_metadata

        # Пути к metadata-файлам.
        self.experiments_path = experiments_path
        self.sessions_path = sessions_path

        # Текущая открытая сессия.
        self.current_session_id: Optional[str] = None

        # Путь к текущему открытому CSV-файлу.
        self.current_path: Optional[Path] = None

        # Открытый файл и CSV writer.
        self.current_file: Optional[TextIO] = None
        self.current_writer: Optional[csv.writer] = None

    def require_device_id(self) -> str:
        """
        Вернуть эффективный device_id.

        Если device_id не задан через CLI и ещё не определён по DEVICE_INFO,
        открывать session-файл нельзя: иначе появятся грязные данные
        под неизвестным устройством.
        """
        if self.effective_device_id:
            return self.effective_device_id

        raise RuntimeError(
            "device_id is not provided and device could not be resolved from DEVICE_INFO. "
            "Provide --device-id or register device MAC in data/metadata/devices.json."
        )

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
        - DEVICE_INFO используется для служебной проверки и enrichment metadata;
        - если --device-id не задан, device_id должен быть найден по devices.json;
        - если найти не удалось, это ошибка.
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

    def _session_path(self, session_id: str) -> Path:
        """
        Построить путь к CSV-файлу сессии.

        Пример:

            base_dir      = data/raw
            experiment_id = EXP01
            device_id     = m5_001
            session_id    = A001

        Результат:

            data/raw/EXP01/m5_001/session_A001.csv
        """
        return (
            self.base_dir
            / self.experiment_id
            / self.require_device_id()
            / f"session_{session_id}.csv"
        )

    def open_session(self, session_id: str, timestamp_ms: str) -> None:
        """
        Открыть CSV-файл для заданной сессии.

        Если был открыт другой файл, он закрывается.

        Если файл новый:
            - создаём папку;
            - пишем CSV header.

        Если включён --create-metadata:
            - создаём черновую запись experiment, если её нет;
            - создаём черновую запись session, если её нет.

        Затем записываем EVENT NEW_SESSION в CSV.
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
                device_id=self.require_device_id(),
            )

            create_draft_session_metadata(
                sessions_path=self.sessions_path,
                experiment_id=self.experiment_id,
                device_id=self.require_device_id(),
                session_id=session_id,
                file_path=path,
                mac_address=self.mac_address,
                firmware_version=self.firmware_version,
                device_registry_record=self.device_registry_record,
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
        Закрыть текущий CSV-файл.

        Вызывается:
        - при переключении на новую сессию;
        - при остановке сервера;
        - при Ctrl+C.
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
        Убедиться, что открыт файл нужной сессии.

        Если пришла строка A002, а открыт файл A001,
        logger переключится на файл A002.
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

        EVENT-строки не содержат ax/ay/az/gx/gy/gz,
        поэтому эти поля остаются пустыми.
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

        EVENT,NEW_SESSION,session_id,timestamp_ms
        EVENT,START,session_id,record_id,timestamp_ms
        EVENT,STOP,session_id,record_id,timestamp_ms,sample_count
    """
    if len(parts) < 3:
        print(f"[WARN] Bad EVENT row: {parts}")
        return

    event_type = parts[1]

    if event_type == "DEVICE_INFO":
        if len(parts) != 5:
            print(f"[WARN] Bad DEVICE_INFO event: {parts}")
            return

        mac_address = parts[2]
        firmware_version = parts[3]
        timestamp_ms = parts[4]

        writer.handle_device_info(
            mac_address=mac_address,
            firmware_version=firmware_version,
            timestamp_ms=timestamp_ms,
        )

        print("[INFO] Received event type: DEVICE_INFO")
        return

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


def handle_protocol_line(line: str, writer: SessionWriter) -> None:
    """
    Обработать одну строку протокола MotionBlocks.

    Эта функция не знает, откуда пришла строка:
    - из Serial;
    - из HTTP;
    - из тестового файла.

    Она работает только с текстовой строкой.

    Примеры строк:

        EVENT,NEW_SESSION,A001,12345
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

    Этот класс вызывается Python HTTP-сервером на каждый входящий запрос.

    Поддерживаем два endpoint:

        GET /health

            Простая проверка, что сервер жив.
            Возвращает "ok".

        POST /line

            Основной endpoint.
            Устройство отправляет сюда одну строку протокола EVENT/DATA.

    Важно:
    writer хранится как class variable:

        MotionBlocksRequestHandler.writer = writer

    Это простой способ дать HTTP handler доступ к SessionWriter.
    """

    writer: SessionWriter

    def log_message(self, format: str, *args) -> None:
        """
        Отключить стандартный HTTP-log.

        По умолчанию BaseHTTPRequestHandler печатает каждое обращение:

            127.0.0.1 - - [date] "POST /line HTTP/1.1" 200 -

        При 10 Hz это быстро засорит консоль.
        Поэтому оставляем только наши осмысленные print().
        """
        return

    def _send_text_response(self, status_code: int, text: str) -> None:
        """
        Отправить простой текстовый HTTP-ответ.

        Например:

            status_code = 200
            text = "ok\n"

        Метод:
        - кодирует текст в UTF-8;
        - выставляет Content-Type;
        - выставляет Content-Length;
        - отправляет body.
        """
        body = text.encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        """
        Обработка GET-запросов.

        Сейчас поддерживается только:

            GET /health

        Он нужен для ручной проверки сервера:

            Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8080/health"

        Ожидаемый ответ:

            ok
        """
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_text_response(200, "ok\n")
            return

        self._send_text_response(404, "not found\n")

    def do_POST(self) -> None:
        """
        Обработка POST-запросов.

        Основной рабочий endpoint:

            POST /line

        Устройство должно отправлять body как plain text:

            EVENT,NEW_SESSION,A001,12345

        или:

            DATA,A001,1,1,13100,0.0123,-0.0341,0.9872,0.1200,-0.0300,0.0100,0.9880

        Алгоритм:
        1. Проверяем, что путь ровно /line.
        2. Читаем Content-Length.
        3. Читаем body заданной длины.
        4. Декодируем body как UTF-8.
        5. Разбиваем body на строки.
        6. Каждую строку передаём в handle_protocol_line().
        7. Возвращаем "ok".
        """
        parsed = urlparse(self.path)

        # Другие POST endpoint пока не поддерживаем.
        if parsed.path != "/line":
            self._send_text_response(404, "not found\n")
            return

        # HTTP-клиент должен сообщить, сколько байт в body.
        # Без Content-Length сервер не знает, сколько читать из входящего потока.
        content_length_header = self.headers.get("Content-Length")

        if content_length_header is None:
            self._send_text_response(411, "missing content length\n")
            return

        try:
            content_length = int(content_length_header)
        except ValueError:
            self._send_text_response(400, "bad content length\n")
            return

        # Читаем ровно content_length байт из HTTP body.
        raw_body = self.rfile.read(content_length)

        # Декодируем body в строку.
        # errors="ignore" нужен, чтобы не падать на случайных мусорных байтах.
        body = raw_body.decode("utf-8", errors="ignore").strip()

        if not body:
            self._send_text_response(400, "empty body\n")
            return

        try:
            # Обычно устройство будет отправлять одну строку на один POST.
            #
            # Но splitlines() позволяет принять и несколько строк сразу.
            # Это полезно для тестов и будущего batch-режима.
            for line in body.splitlines():
                handle_protocol_line(line, self.writer)

        except Exception as exc:
            # Если что-то пошло не так, печатаем ошибку в консоль
            # и возвращаем HTTP 500.
            print(f"[ERROR] Failed to handle request: {exc}")
            self._send_text_response(500, f"error: {exc}\n")
            return

        # Если все строки обработаны успешно — отвечаем ok.
        self._send_text_response(200, "ok\n")


def main() -> None:
    """
    Основная функция программы.

    Делает 5 вещей:

    1. Читает параметры командной строки.
    2. Создаёт SessionWriter.
    3. Передаёт SessionWriter в HTTP handler.
    4. Создаёт ThreadingHTTPServer.
    5. Запускает бесконечный цикл ожидания HTTP-запросов.

    Остановка:

        Ctrl+C
    """

    # --------------------------------------------------------
    # 1. Параметры командной строки
    # --------------------------------------------------------
    parser = argparse.ArgumentParser(description="MotionBlocks HTTP Logger")

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind. Use 0.0.0.0 to accept requests from other devices in the network.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port",
    )
    parser.add_argument(
        "--experiment-id",
        required=True,
        help="Experiment id, for example EXP01",
    )
    parser.add_argument(
        "--device-id",
        required=False,
        default=None,
        help="Device id, for example m5_001. If omitted, logger resolves device_id from DEVICE_INFO and devices.json.",
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
    parser.add_argument(
        "--devices-path",
        default="data/metadata/devices.json",
        help="Path to device registry JSON file",
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # 2. Создаём объект записи данных
    #
    # Он будет заниматься CSV и metadata.
    # HTTP-сервер будет только принимать строки и передавать их сюда.
    # --------------------------------------------------------
    writer = SessionWriter(
        base_dir=Path(args.base_dir),
        experiment_id=args.experiment_id,
        device_id=args.device_id,
        create_metadata=args.create_metadata,
        experiments_path=Path(args.experiments_path),
        sessions_path=Path(args.sessions_path),
        devices_path=Path(args.devices_path),
    )

    # --------------------------------------------------------
    # 3. Передаём writer в HTTP handler
    #
    # BaseHTTPRequestHandler создаёт новый handler object
    # на каждый запрос, поэтому напрямую передать writer в __init__
    # неудобно.
    #
    # Простой вариант для нашего учебного logger:
    # сохранить writer как class variable.
    # --------------------------------------------------------
    MotionBlocksRequestHandler.writer = writer

    # --------------------------------------------------------
    # 4. Создаём HTTP-сервер
    #
    # ThreadingHTTPServer обрабатывает запросы в отдельных потоках.
    # Для 10 Hz это с запасом.
    #
    # host:
    #   127.0.0.1 — принимать только локальные запросы с этого ноутбука.
    #   0.0.0.0   — принимать запросы с других устройств в сети.
    #
    # Для M5StickC нужен именно 0.0.0.0.
    # --------------------------------------------------------
    server = ThreadingHTTPServer(
        (args.host, args.port),
        MotionBlocksRequestHandler,
    )

    # --------------------------------------------------------
    # 5. Печатаем параметры запуска
    # --------------------------------------------------------
    print("MotionBlocks HTTP Logger")
    print(f"Host:            {args.host}")
    print(f"Port:            {args.port}")
    print(f"Experiment id:   {args.experiment_id}")
    print(f"Device id:       {args.device_id if args.device_id else '(auto from DEVICE_INFO)'}")
    print(f"Devices:         {args.devices_path}")
    print(f"Base dir:        {args.base_dir}")
    print(f"Create metadata: {args.create_metadata}")
    print(f"Experiments:     {args.experiments_path}")
    print(f"Sessions:        {args.sessions_path}")
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
        # ----------------------------------------------------
        # Главный цикл HTTP-сервера.
        #
        # Эта строка блокирует выполнение программы.
        # Программа будет ждать входящие HTTP-запросы,
        # пока пользователь не нажмёт Ctrl+C.
        # ----------------------------------------------------
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("Stopping HTTP logger...")

    finally:
        # ----------------------------------------------------
        # Аккуратное завершение:
        # - закрываем HTTP-сервер;
        # - закрываем текущий CSV-файл.
        # ----------------------------------------------------
        server.server_close()
        writer.close_session()
        print("HTTP logger stopped.")


if __name__ == "__main__":
    main()
