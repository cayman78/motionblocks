# Takeaway — Multi-network WiFi и mDNS discovery логгера

## Date

2026-06-15

## Type

architecture-decision

## Status

Accepted — решение принято, реализация отложена

---

## Context

Комбинация M5StickC Plus2 + компьютер с логгером используется в разных сетях
(дом, мобильная точка доступа, другие места). Сейчас параметры сети хранятся
в `wifi_config.h` — один SSID, один пароль, один `LOGGER_URL`.

При смене сети требуется перепрошивка устройства. Это неудобно и неправильно.

---

## Understanding

**Правильная модель:** устройство само определяет доступные сети и подключается
к той из них, параметры которой есть в его списке.

**Проблема LOGGER_URL:** IP компьютера меняется в каждой сети — решать
только WiFi без решения адресации логгера бессмысленно.

---

## Decision

**Основной путь: mDNS**

Компьютер объявляет себя как `motionblocks.local`.
Устройство ищет логгер по имени, не по IP.
Работает в любой сети без изменений конфигурации.

Реализация:
- Python: библиотека `zeroconf`
- ESP32: `ESPmDNS.h` (поддержка из коробки)

**Fallback: URL per network в JSON**

Если mDNS не сработал (некоторые роутеры блокируют, мобильная точка доступа
может изолировать клиентов) — брать `logger_url` из записи сети в JSON.

---

## Architecture

Новый файл конфигурации (хранится в SPIFFS на ESP32):

```json
[
  {
    "ssid": "HomeNetwork",
    "password": "...",
    "logger_url": "http://192.168.1.100:8080/line"
  },
  {
    "ssid": "MobileHotspot",
    "password": "...",
    "logger_url": "http://192.168.43.100:8080/line"
  }
]
```

Логика подключения устройства:

```text
1. Сканировать доступные сети (WiFi.scanNetworks)
2. Найти пересечение с wifi_networks.json
3. Подключиться (по убыванию RSSI если несколько известных сетей доступны)
4. Попробовать разрезолвить motionblocks.local через mDNS
5. Если mDNS не сработал — использовать logger_url из JSON для этой сети
```

`wifi_config.h` заменяется на `wifi_networks.json` в SPIFFS.
Файл не коммитится в Git (содержит пароли).
В репозитории остаётся только `wifi_networks.example.json`.

---

## Why mDNS over broadcast discovery

Broadcast не выбран как основной путь:
- некоторые роутеры блокируют broadcast между клиентами
- мобильная точка доступа часто изолирует клиентов
- mDNS надёжнее в большинстве домашних сетей и проще в реализации

---

## Implications

- Перепрошивка при смене сети больше не нужна
- Новую сеть можно добавить через обновление JSON в SPIFFS (без перекомпиляции)
- `http_logger.py` при старте регистрирует себя как `motionblocks.local`
- Устройство становится по-настоящему portable

---

## Recommended Branch

```text
feature/multi-network-wifi
```

## Tags

#motionblocks #wifi #mdns #firmware #transport #tech-debt #architecture-decision

## Related

- `knowledge/takeaways/2026-06-09_wireless-transport-choice.takeaways.md`
- `firmware/m5stickc-plus2/src/wifi_config.h` — заменяется на SPIFFS JSON
