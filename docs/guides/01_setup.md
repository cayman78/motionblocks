# Настройка окружения — MotionBlocks

Этот документ описывает первоначальную настройку рабочего окружения для работы с проектом MotionBlocks на Windows.

---

## Что потребуется

- Windows 10 или 11
- Устройство M5StickC Plus2
- USB-кабель для подключения устройства
- Доступ к локальной Wi-Fi сети

---

## 1. Git

Скачай и установи Git для Windows: https://git-scm.com/download/win

Во время установки можно оставить все настройки по умолчанию.

Проверь установку в PowerShell:

```powershell
git --version
```

Клонируй репозиторий:

```powershell
git clone https://github.com/stofendez/motionblocks.git
cd motionblocks
```

---

## 2. VS Code

Скачай и установи VS Code: https://code.visualstudio.com

После установки открой папку репозитория:

```powershell
code .
```

---

## 3. PlatformIO

PlatformIO — среда для прошивки микроконтроллеров. Устанавливается как расширение VS Code.

В VS Code открой раздел Extensions (`Ctrl+Shift+X`), найди **PlatformIO IDE** и установи.

После установки перезапусти VS Code.

Проверь установку в PowerShell:

```powershell
pio --version
```

При первом открытии проекта PlatformIO автоматически скачает нужные платформы и библиотеки. Это может занять несколько минут.

---

## 4. Python и виртуальное окружение

Скачай и установи Python 3.10 или новее: https://www.python.org/downloads/

При установке обязательно поставь галочку **Add Python to PATH**.

Проверь установку:

```powershell
python --version
```

Создай виртуальное окружение в корне репозитория:

```powershell
cd C:\путь\к\motionblocks
python -m venv .venv
```

Активируй окружение:

```powershell
.\.venv\Scripts\Activate.ps1
```

Если PowerShell блокирует выполнение скриптов, выполни один раз:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

После активации в начале строки появится `(.venv)`.

Установи зависимости:

```powershell
pip install pyserial requests flask pandas matplotlib streamlit
```

---

## 5. Драйвер USB

M5StickC Plus2 использует чип CH9102. Если устройство не определяется в системе, скачай и установи драйвер: https://www.wch-ic.com/downloads/CH343SER_EXE.html

После установки подключи устройство по USB. В диспетчере устройств оно должно появиться как COM-порт (например, COM6).

---

## 6. Настройка Wi-Fi

В папке `firmware/m5stickc-plus2/src/` скопируй файл примера:

```powershell
copy firmware\m5stickc-plus2\src\wifi_config.example.h firmware\m5stickc-plus2\src\wifi_config.h
```

Открой `wifi_config.h` и заполни свои данные:

```cpp
#define WIFI_SSID     "название_сети"
#define WIFI_PASSWORD "пароль"
#define LOGGER_URL    "http://192.168.1.100:8080/line"
```

IP-адрес в `LOGGER_URL` — это адрес твоего ноутбука в локальной сети. Узнать его можно командой:

```powershell
ipconfig
```

Найди строку **IPv4-адрес** для своего Wi-Fi адаптера.

`wifi_config.h` добавлен в `.gitignore` и не попадает в репозиторий — твои данные Wi-Fi останутся локальными.

---

## 7. Реестр устройств

Открой файл `data/metadata/devices.json` и добавь своё устройство:

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

MAC-адрес устройства отображается на экране при первом включении, а также виден в Serial Monitor после прошивки в строке `EVENT,DEVICE_INFO`.

---

## 8. Компиляция и прошивка

Подключи устройство по USB. Прошей через PowerShell из корня репозитория:

```powershell
pio run --target upload --upload-port COM6
```

Замени `COM6` на номер своего порта — его можно посмотреть в диспетчере устройств Windows.

После прошивки устройство перезагрузится и покажет стартовый экран **MOTIONBLOCKS LOGGER**.

---

## 9. Сетевой профиль Windows

Чтобы M5StickC мог отправлять данные на ноутбук через Wi-Fi, сетевой профиль должен быть **Частный** (Private).

Проверить и изменить: **Параметры → Сеть и Интернет → Wi-Fi → название сети → Тип сетевого профиля**.

Если профиль Public, брандмауэр Windows заблокирует входящие подключения от устройства.

---

## Ежедневный старт

Каждый раз при открытии нового терминала:

```powershell
cd C:\путь\к\motionblocks
.\.venv\Scripts\Activate.ps1
```

После этого можно запускать Python-инструменты проекта.
