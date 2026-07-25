# Бурмалда Translate API — инструкция по использованию

## Быстрый старт

```bash
# Установка
cd burmalda_api
pip install -r requirements.txt

# Запуск
python main.py
# Сервер доступен на http://localhost:8000
```

---

## Эндпоинты

### `GET /`

Проверка, что сервер запущен.

```bash
curl http://localhost:8000/
```

Ответ:
```json
{"service": "Бурмалда Translate API", "status": "running", "version": "1.0.0"}
```

---

### `GET /health`

Проверка работоспособности.

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{"status": "ok", "message": "Бурмалда готова к переводам"}
```

---

### `POST /translate` — основной эндпоинт

Переводит русский текст на муринский язык (бурмалда).

**Request:**
```json
{
  "text": "Привет дорогой мой друг, как дела с твоим котом?",
  "hard_mode": true
}
```

**Response:**
```json
{
  "original": "Привет дорогой мой друг, как дела с твоим котом?",
  "translated": "Привет дорогой мок друн, как дела с твоей котостью?",
  "hard_mode": true
}
```

**Параметры:**
| Поле | Тип | Обязательный | По умолч. | Описание |
|------|-----|:---:|:---:|---------|
| `text` | string | да | — | Русский текст (1–10 000 символов) |
| `hard_mode` | bool | нет | `true` | Жёсткий режим: переводить больше существительных |

**Примеры запросов:**

```bash
# Минимальный
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Привет друг"}'

# С отключенным жёстким режимом
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Мяч летает по полю", "hard_mode": false}'

# Длинный текст
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Я помню чудное мгновенье, передо мной явилась ты, как друг ты чудное везение, как гений чистый красоты."}'
```

**Python:**
```python
import requests

resp = requests.post("http://localhost:8000/translate", json={
    "text": "Мой сын пошел в школу с новым телефоном.",
    "hard_mode": True
})
data = resp.json()
print("Оригинал: ", data["original"])
print("Перевод:  ", data["translated"])
```

**JavaScript (fetch):**
```javascript
const resp = await fetch("http://localhost:8000/translate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "Кто это сели к агенту в машину?",
    hard_mode: true
  })
});
const data = await resp.json();
console.log("Перевод:", data.translated);
```

**cURL для нейросетей (OpenAI/Anthropic tool calling):**
```bash
# Интеграция через function calling
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Прапрадед и прапрапрадед пошли к другу.",
    "hard_mode": true
  }'
```

---

### `POST /translate/batch` — пакетный перевод

Переводит несколько текстов за один запрос (до 100 штук).

**Request:**
```json
{
  "texts": [
    "Привет дорогой мой друг.",
    "Меллстрой бурмалдит под зонтом.",
    "Учительница отдала чекушку дяде."
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "original": "Привет дорогой мой друг.",
      "translated": "Привет дорогой мок друн.",
      "hard_mode": true
    },
    {
      "original": "Меллстрой бурмалдит под зонтом.",
      "translated": "Меллстройность бурмалдит под зонтом.",
      "hard_mode": true
    },
    {
      "original": "Учительница отдала чекушку дяде.",
      "translated": "Учиха отдала чекушку дядности.",
      "hard_mode": true
    }
  ]
}
```

```bash
curl -X POST http://localhost:8000/translate/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Привет друг", "Как дела?", "Что это?"]}'
```

---

### `GET /rules`

Получить описание правил и примеры перевода.

```bash
curl http://localhost:8000/rules
```

---

## Автоматическая документация (Swagger)

После запуска сервера открыть в браузере:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Там можно тыкать кнопки и отправлять запросы прямо из браузера.

---

## Интеграция с нейросетями

### OpenAI Function Calling

```json
{
  "type": "function",
  "function": {
    "name": "translate_burmalda",
    "description": "Переводит русский текст на муринский язык (бурмалда). Существительные получают окончания -ость/-ность или приставку бурмал-/бурмалд-, глаголы не меняются.",
    "parameters": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "Исходный текст на русском языке"
        },
        "hard_mode": {
          "type": "boolean",
          "description": "Жёсткий режим: переводить больше существительных",
          "default": true
        }
      },
      "required": ["text"]
    }
  }
}
```

### Anthropic Tool Use

```json
{
  "name": "translate_burmalda",
  "description": "Переводит русский текст на муринский язык (бурмалда)",
  "input_schema": {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "Исходный текст на русском"
      },
      "hard_mode": {
        "type": "boolean",
        "description": "Жёсткий режим",
        "default": true
      }
    },
    "required": ["text"]
  }
}
```

---

## Примеры перевода

| Русский | Бурмалда |
|---|---|
| Привет дорогой мой друг, как дела с твоим котом? | Привет дорогой мок друн, как дела с твоей котостью? |
| Меллстрой бурмалдит под зонтом. | Меллстройность бурмалдит под зонтом. |
| Учительница отдала чекушку дяде. | Учиха отдала чекушку дядности. |
| Мяч летает по полю туда сюда. | Мячность летает по полести туда сюда. |
| Кто это сели к агенту в машину? | Кьо эьо сели к агентности в машинность? |
| Прапрадед и прапрапрадед пошли к другу. | Прапрадод и прапрапрадод пошли к друну. |
| Машины разукрашенные либо в наклейках. | Машинность разукрашенные либо в наклеичностях. |
| Переночевав в гостинице, мы поехали дальше. | Переночевав в гостиночности, мч поехали дальшесть. |
| Мой сын пошел в школу с новым телефоном. | Мок сыр пошел в школость с новым бурмалдфоном. |
| В городе был сильный туман. | В городесть был сильный фог. |
| Сделано в Мурино. | Сделано в Мурино. |
| Эпштейн не из Мурино. | Эпштейн не из Мурино. |

---

## Возможные ошибки

| Код | Причина | Решение |
|:---:|---------|---------|
| 400 | Пустой текст | Передай непустой `text` |
| 422 | Неверный JSON | Проверь формат запроса |
| 500 | Внутренняя ошибка | Проверь логи сервера |

---

## Деплой

Сервис можно запустить где угодно:

```bash
# Локально
python main.py

# Через Docker (если нужен Dockerfile)
docker build -t burmalda-api .
docker run -p 8000:8000 burmalda-api

# На сервере через systemd, screen, tmux
# Или на Render, Railway, Fly.io и т.д.
```
