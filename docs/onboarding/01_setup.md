    # Настройка окружения — MotionBlocks

Этот документ описывает первоначальную настройку рабочего окружения для работы с проектом MotionBlocks на Windows.

---

## Что потребуется

- Windows 10 или 11
- Устройство M5StickC Plus2
- USB-C кабель для подключения устройства
- Доступ к локальной Wi-Fi сети

---

## 1. Регистрация на GitHub

Если аккаунт уже есть — пропусти этот пункт.

1. Зайди на https://github.com
2. Нажми **Sign up**
3. Выбери username — он будет виден в истории коммитов и в URL
4. Сообщи свой username владельцу проекта — он выдаст права на push

---

## 2. Git

Скачай и установи Git для Windows: https://git-scm.com/download/win

Во время установки можно оставить все настройки по умолчанию.

Проверь установку в PowerShell:

```powershell
git --version
```

Настрой имя и email:

```powershell
git config --global user.name "Твоё Имя"
git config --global user.email "твой@email.com"
```

`user.name` — это подпись в коммитах, необязательно совпадает с GitHub username. GitHub username используется для авторизации, имя в коммитах — для читаемости истории. Это разные вещи.

---

## 3. Клонирование репозитория

Команда `git clone` скачивает репозиторий с GitHub и создаёт папку `motionblocks` со всеми файлами проекта внутри той папки, из которой она вызвана. Это одноразовая операция — после клонирования папка живёт локально на твоём компьютере.

Дальнейшая работа с проектом (получение обновлений, отправка изменений) делается через команды Git — они описаны в [03_git-workflow.md](03_git-workflow.md).

Сначала перейди в папку где будут лежать твои проекты:

```powershell
cd C:\Users\ИМЯ\Documents\projects
```

Затем клонируй репозиторий:

```powershell
git clone https://github.com/cayman78/motionblocks.git
cd motionblocks
```

После клонирования переключись на рабочую ветку:

```powershell
git checkout dev
```

---

## 4. VS Code

Скачай и установи VS Code: https://code.visualstudio.com

После установки открой папку репозитория:

```powershell
code .
```

Рекомендуемые расширения — установи через панель Extensions (Ctrl+Shift+X):

| Расширение | ID |
|---|---|
| PlatformIO IDE | `platformio.platformio-ide` |
| Python | `ms-python.python` |
| Markdown Preview Enhanced | `shd101wyy.markdown-preview-enhanced` |
| GitLens | `eamodio.gitlens` |

---

## 5. PlatformIO

PlatformIO — среда для прошивки микроконтроллеров. Устанавливается как расширение VS Code (см. выше).

После установки перезапусти VS Code.

Проверь установку в терминале:

```powershell
pio --version
```

При первом открытии проекта PlatformIO автоматически скачает нужные платформы и библиотеки. Это может занять несколько минут.

---

## 6. Python и виртуальное окружение

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
pip install pyserial requests flask pandas matplotlib streamlit zeroconf
```

---

## 7. Драйвер USB

M5StickC Plus2 использует чип CH9102. Если устройство не определяется в системе, скачай и установи драйвер: https://www.wch-ic.com/downloads/CH343SER_EXE.html

После установки подключи устройство по USB. В диспетчере устройств оно должно появиться как COM-порт (например, COM6):

```powershell
devmgmt.msc
```

Ищи раздел **Ports (COM & LPT)** → **USB-Enhanced-SERIAL CH9102 (COMx)**.

---

## 8. Настройка Wi-Fi

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

IP-адрес в `LOGGER_URL` — это адрес твоего компьютера в локальной сети. Узнать его можно командой:

```powershell
ipconfig
```

Найди строку **IPv4-адрес** для своего Wi-Fi адаптера.

`wifi_config.h` добавлен в `.gitignore` и не попадает в репозиторий — твои данные Wi-Fi останутся локальными.

**Рекомендация:** привяжи фиксированный локальный IP к своему компьютеру в настройках роутера (DHCP reservation). Это делается один раз — и IP компьютера в домашней сети больше не меняется. Иначе при каждом переподключении IP может измениться и придётся обновлять `wifi_config.h`.

---

## 9. Сетевой профиль Windows

Чтобы M5StickC мог отправлять данные на компьютер через Wi-Fi, сетевой профиль должен быть **Частный** (Private).

Проверить и изменить: **Параметры → Сеть и Интернет → Wi-Fi → название сети → Тип сетевого профиля**.

Если профиль Public — брандмауэр Windows заблокирует входящие подключения от устройства.

---

## 10. Компиляция и прошивка

Открой папку проекта в VS Code: **File → Open Folder** → выбери папку `motionblocks`.

В левой панели VS Code появится иконка PlatformIO — голова муравья (🐜). Нажми на неё.

Открой терминал: **Terminal → New Terminal**.

Перейди в папку firmware:

```powershell
cd firmware/m5stickc-plus2
```

Команда `pio run` берёт файл `src/main.cpp` где собрана вся логика устройства и компилирует его. После этого `pio run --target upload` записывает прошивку в память устройства через USB.

Сборка:

```powershell
pio run
```

Прошивка (замени COM6 на твой порт):

```powershell
pio run --target upload --upload-port COM6
```

После прошивки устройство перезагрузится автоматически.

---

## 11. Orange Data Mining (для ML экспериментов)

Orange — визуальный инструмент для машинного обучения без кода.

Скачай и установи: https://orangedatamining.com/download/

Выбери **Windows installer** (.exe). Python встроен, отдельная установка не нужна.

---

## 12. Работа с Markdown файлами

Вся документация проекта написана в формате Markdown (`.md` файлы). Это обычный текст с простой разметкой — читается даже в сыром виде, но с просмотрщиком намного удобнее.

Краткое руководство по Markdown: [00_markdown_guide.md](00_markdown_guide.md)

### VS Code

Открой любой `.md` файл. Нажми `Ctrl+Shift+V` — откроется панель предпросмотра.

Режим split (редактор + предпросмотр рядом): `Ctrl+K`, затем `V`.

### Obsidian

Obsidian — отдельное приложение специально для Markdown. Удобен для навигации по большому количеству документов.

Скачай: https://obsidian.md

После установки: **Open folder as vault** → выбери папку `motionblocks`. Все `.md` файлы проекта будут доступны в виде дерева с поиском и навигацией.

---

## Ежедневный старт

Каждый раз при открытии нового терминала:

```powershell
cd C:\путь\к\motionblocks
.\.venv\Scripts\Activate.ps1
```

После этого можно запускать Python-инструменты проекта.

---

## Следующий шаг

→ [02_hardware_and_data.md](02_hardware_and_data.md) — работа с устройством и данными
