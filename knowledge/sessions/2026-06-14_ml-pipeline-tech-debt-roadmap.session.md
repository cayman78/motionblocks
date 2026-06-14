# Session Summary

## Session

Date: 2026-06-14
Project: MotionBlocks
Topic: ML pipeline, tech debt, дорожная карта, долгосрочное видение

---

## Starting Context

Firmware v0.8.0 с async HTTP работал. Данные EXP14 собраны и прошли анализ
(все OK, 100 Hz, gaps = 0). Нужно было двигаться к ML эксперименту.
Также накопился tech debt по firmware и motion_browser.

---

## Topics Discussed

- compute_features.py — скользящее окно, параметры, feature_config.json
- Первый ML эксперимент в Orange Data Mining
- Confusion matrix и интерпретация результатов
- Predictions на новых данных EXP15
- Tech debt: батарея, NEXT REC, удаление записей, movement_type
- Firmware v0.8.1 — redesign экранов READY и REC
- Дорожная карта проекта — фазы 1-4
- Железо: ограничения M5StickC, варианты продления автономности
- Следующий проект — суточный мониторинг, anomaly detection
- Медицинский мониторинг — EWS, пациенты, пожилые
- Своё устройство — accessibility design, JLCPCB, гранты
- Branding: Stofendez Lab, 100FNDZ

---

## Key Decisions

**ML pipeline:**
- Скользящее окно: 2s / шаг 0.5s / обрезка 1s с каждой стороны
- Параметры в `feature_config.json`, переопределяются через CLI
- Output features.csv → `data/analysis/features/` (не `data/features/`)
- Компенсация g — отложить. Сначала простые фичи, потом смотреть где проблемы
- FFT фичи — следующий шаг после базового эксперимента

**Orange результат:**
- CA = 99.5% на обучающих данных (EXP14)
- ~70% на новых данных (EXP15) — ожидаемо для одного субъекта
- Малые классы (1-3 примера) не работают — нужно добирать или убирать
- EXP15 — проверка качества, не добавлять в обучение

**Tech debt — всё закрыто в этой ветке:**
- Батарея: `M5.Power.getBatteryLevel()` на READY и REC
- NEXT REC: SESSION и REC в одну строку на READY, номер записи рядом
- Удаление записей: multiselect по record_id в motion_browser.py
- movement_type: text_input + selectbox-подсказки в редакторе
- features.csv перенесён в `data/analysis/features/`

**Firmware v0.8.1:**
- `drawStatusBar()` — общая верхняя строка для READY и REC
- Убран зелёный кружок Wi-Fi с REC экрана (конфликтовал с батареей)
- REC экран получил ту же верхнюю строку что и READY

**Дорожная карта:**
- Приоритет: датасет → FFT → scikit-learn → Edge Impulse → Guardian PoC
- serial_logger.py — низкий приоритет, держим в уме
- Guardian PoC на M5StickC достаточен для демонстрации и конкурса
- Следующий проект (суточный мониторинг) — Android / Samsung Watch

**Железо:**
- M5StickC: доп аккумулятор на ремешке + SD карта = реальный вариант
- Android — правильный выбор для суточного профилирования
- XIAO nRF52840 — конечная точка если нужно своё устройство под пром
- Своё устройство через JLCPCB — реально при наличии гранта

**Медицинский мониторинг:**
- Постановка: непрерывный EWS как альтернатива ручному NEWS2
- Сенсоры: IMU (есть) + MAX30102 (пульс/SpO2) + MLX90614 (температура)
- MAX30102 подключается к M5StickC через Grove — один провод
- Accessibility design: большая кнопка SOS, крупный экран, автономность

**Branding:**
- Stofendez Lab — официальное название (придумал ребёнок в 3 года)
- 100FNDZ — короткий идентификатор / хэштег
  (100 = Sto = Stofendez, читается как "100 friends")

---

## Artifacts Created or Updated

Созданы:

- `tools/compute_features.py` — извлечение фич, скользящее окно
- `data/metadata/feature_config.json` — параметры окна по умолчанию
- `knowledge/takeaways/2026-06-14_project-roadmap-and-vision.takeaways.md`
  — дорожная карта, железо, медмониторинг, JLCPCB, 100FNDZ

Обновлены:

- `firmware/m5stickc-plus2/src/main.cpp` → v0.8.1
  (батарея, NEXT REC, статус-бар, redesign экранов)
- `tools/motion_browser.py`
  (удаление записей из CSV, свободный ввод movement_type)
- `tools/compute_features.py`
  (feature_config.json, time_from_record_start_sec,
   output в data/analysis/features/)

---

## Open Questions

- Когда добавлять MAX30102 — после Guardian PoC или параллельно?
- Какой конкурс / олимпиада подходит для участия по возрасту ребёнка?
- SD карта для M5StickC — нужна отдельная прошивка или расширение текущей?
- Когда начинать Android / Samsung Watch эксперименты?

---

## Next Steps

1. Собрать расширенный датасет — несколько субъектов, 10+ записей на класс
2. Добавить FFT фичи в `compute_features.py`
3. scikit-learn baseline — воспроизводимая модель в коде
4. Edge Impulse — firmware_2_classifier, real-time на устройстве
5. Guardian PoC — firmware_3_guardian, тревожная кнопка + автосрабатывание
6. Большой коммит текущей ветки feature/ml-pipeline

---

## Related Artifacts

- `knowledge/takeaways/2026-06-14_project-roadmap-and-vision.takeaways.md`
- `knowledge/takeaways/2026-06-14_http-blocks-imu-sampling-async-fix.takeaways.md`
- `firmware/m5stickc-plus2/src/main.cpp` (v0.8.1)
- `tools/compute_features.py`
- `tools/motion_browser.py`
- `data/metadata/feature_config.json`

---

## Observations

Первый ML результат получен за одну сессию от сырых данных до
Confusion Matrix в Orange. CA 99.5% на обучающих данных —
сильный результат для первого эксперимента.

70% на новых данных — честный и ожидаемый результат.
Модель обучена на одном субъекте. Это сама по себе интересная
исследовательская тема: subject generalization.

Название 100FNDZ — неожиданно сильный брендинг.
История происхождения (рок-группа трёхлетнего ребёнка)
работает как конкурсная история.

Проект вырос за эту сессию от "логгер движений"
до "носимая медицинская система мониторинга с научным заделом".
