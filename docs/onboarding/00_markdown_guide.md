# Markdown: краткая инструкция

## 1. Что такое Markdown

**Markdown** — это простой текстовый формат разметки. Файл Markdown обычно имеет расширение `.md`.

Markdown удобен для README-файлов в GitHub, проектной документации, журналов работ, технических заметок, takeaways для LLM и простых инструкций.

Главная идея: файл остаётся обычным текстом, но специальные символы задают структуру документа.

---

## 2. Заголовки

Заголовки задаются символом `#`.

```markdown
# Заголовок 1 уровня

## Заголовок 2 уровня

### Заголовок 3 уровня
```

Обычно в документе используют:

```markdown
# Название документа
## Основной раздел
### Подраздел
```

---

## 3. Абзацы

Обычный текст пишется как есть.

```markdown
Это первый абзац.

Это второй абзац.
```

Между абзацами оставляют пустую строку.

---

## 4. Жирный и курсив

```markdown
**жирный текст**

*курсив*

***жирный курсив***
```

---

## 5. Списки

Маркированный список:

```markdown
- первый пункт
- второй пункт
- третий пункт
```

Вложенный список:

```markdown
- первый пункт
  - подпункт
  - подпункт
- второй пункт
```

Нумерованный список:

```markdown
1. Первый шаг
2. Второй шаг
3. Третий шаг
```

---

## 6. Чек-листы

Чек-листы удобны для Definition of Done и задач.

```markdown
- [x] Сделано
- [ ] Не сделано
- [ ] Проверить позже
```

Пример:

- [x] Прошивка компилируется
- [x] Устройство отправляет данные
- [ ] Python logger сохраняет CSV

---

## 7. Код внутри строки

Для коротких фрагментов кода используют обратные кавычки:

```markdown
Файл `main.cpp` лежит в папке `src/`.
```

Результат:

Файл `main.cpp` лежит в папке `src/`.

---

## 8. Блоки кода

Для больших фрагментов используют тройные обратные кавычки.

````markdown
```cpp
#include <M5Unified.h>

void setup() {
    M5.begin();
}
```
````

Можно указывать язык: `cpp`, `python`, `json`, `csv`, `powershell`, `text`.

Пример Python:

```python
print("Hello, MotionBlocks")
```

Пример PowerShell:

```powershell
pio run
pio run --target upload --upload-port COM6
```

---

## 9. Таблицы

```markdown
| Поле | Описание |
|---|---|
| experiment_id | Код эксперимента |
| session_id | Код сессии |
| record_id | Номер попытки |
```

Результат:

| Поле | Описание |
|---|---|
| experiment_id | Код эксперимента |
| session_id | Код сессии |
| record_id | Номер попытки |

---

## 10. Ссылки

```markdown
[GitHub](https://github.com)
```

---

## 11. Изображения

```markdown
![Описание изображения](images/example.png)
```

Если изображение лежит рядом с документом:

```markdown
![Схема](diagram.png)
```

---

## 12. Цитаты

```markdown
> Это цитата или важное замечание.
```

Результат:

> Это цитата или важное замечание.

---

## 13. Горизонтальная линия

```markdown
---
```

Используется для разделения крупных блоков.

---

## 14. Пример структуры README.md

````markdown
# MotionBlocks

## Goal

Short project description.

## Hardware

- M5StickC Plus2
- IMU sensor

## Firmware

Project location:

```text
firmware/m5stickc-plus2
```

Build:

```powershell
pio run
```

Upload:

```powershell
pio run --target upload --upload-port COM6
```

## Data

Raw data path:

```text
data/raw/EXP01/m5_001/session_A001.csv
```

## Status

- [x] First firmware works
- [x] IMU logger works
- [ ] Python serial logger
````

---

## 15. Пример проектной записи в journal.md

```markdown
## 2026-06-10 — Session-aware IMU logger v0.3

### Context

Continued development of MotionBlocks firmware.

### Result

Session-aware firmware works.

### Confirmed

- [x] firmware builds
- [x] Button A starts and stops records
- [x] Button B switches sessions
- [x] Serial protocol includes session_id, record_id, sample_id

### Next step

Implement Python serial logger.
```

---

## 16. Где смотреть Markdown

### VS Code

В VS Code можно открыть предпросмотр Markdown:

```text
Ctrl + Shift + V
```

Или через контекстное меню:

```text
Right click → Open Preview
```

Можно открыть предпросмотр рядом с исходником:

```text
Ctrl + K, затем V
```

### GitHub

GitHub автоматически красиво показывает файлы:

```text
README.md
*.md
```

Это основной способ просмотра проектной документации.

### Obsidian

Obsidian удобен для базы знаний и связанных заметок. Подходит для личных заметок, проектного knowledge base и связанных документов.

### Typora / MarkText

Редакторы, где Markdown редактируется почти как обычный документ. Удобны для чтения и быстрой правки, но для проекта с Git чаще достаточно VS Code.

---

## 17. Практические правила для MotionBlocks

1. Один документ — одна понятная тема.
2. В начале документа — заголовок `#`.
3. Для команд всегда использовать блоки кода.
4. Для путей использовать `text` или inline-code.
5. Для статуса использовать чек-листы.
6. Не писать длинные полотна текста без разделов.
7. Для LLM takeaways использовать короткие структурированные Markdown-файлы.
8. Для журнала использовать хронологические записи.

---

## 18. Рекомендуемые расширения файлов

```text
README.md                         — обзор проекта
docs/journal.md                   — журнал работ
docs/stage_1_plan.md              — план этапа
llm/takeaways/*.takeaways.md      — выводы из обсуждений
llm/context/current_state.md      — текущее состояние проекта
```

---

## 19. Минимальный шаблон Markdown-документа

```markdown
# Document title

## Purpose

Short explanation of why this document exists.

## Content

Main information.

## Decisions

- Decision 1
- Decision 2

## Next steps

- [ ] Step 1
- [ ] Step 2
```
