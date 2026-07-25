from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from translator import translate_text

app = FastAPI(
    title="Бурмалда Translate API",
    description="API для перевода русского текста на муринский язык (бурмалда). "
                "Мемный переводчик с правилами: исключения, приставки бурмал-/бурмалд-, "
                "окончания -ость/-ность и защита глаголов.",
    version="1.0.0",
    contact={
        "name": "Burmalda Translate",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranslateRequest(BaseModel):
    text: str = Field(..., description="Исходный текст на русском языке", min_length=1, max_length=10000)
    hard_mode: bool = Field(
        default=True,
        description="Жёсткая бурмалда: переводить большинство существительных. "
                    "False = только словарные исключения и явные модели."
    )


class TranslateResponse(BaseModel):
    original: str = Field(..., description="Исходный текст")
    translated: str = Field(..., description="Перевод на муринский язык")
    hard_mode: bool = Field(..., description="Какой режим использовался")


class BatchTranslateRequest(BaseModel):
    texts: list[str] = Field(..., description="Список текстов для перевода", min_length=1, max_length=100)


class BatchTranslateResponse(BaseModel):
    results: list[TranslateResponse]


class TranslateError(BaseModel):
    error: str


@app.get("/", tags=["Health"])
async def root():
    return {"service": "Бурмалда Translate API", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "message": "Бурмалда готова к переводам"}


@app.post("/translate", response_model=TranslateResponse, tags=["Translation"])
async def translate(request: TranslateRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")

    try:
        result = translate_text(request.text, hard=request.hard_mode)
        return TranslateResponse(
            original=request.text,
            translated=result,
            hard_mode=request.hard_mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка перевода: {str(e)}")


@app.post("/translate/batch", response_model=BatchTranslateResponse, tags=["Translation"])
async def translate_batch(request: BatchTranslateRequest):
    results = []
    for text in request.texts:
        try:
            result = translate_text(text, hard=True)
            results.append(TranslateResponse(
                original=text,
                translated=result,
                hard_mode=True,
            ))
        except Exception as e:
            results.append(TranslateResponse(
                original=text,
                translated=f"[Ошибка: {str(e)}]",
                hard_mode=True,
            ))
    return BatchTranslateResponse(results=results)


@app.get("/rules", tags=["Info"])
async def get_rules():
    return {
        "description": "Бурмалда Translate — мемный переводчик русского языка на муринский язык.",
        "rules": [
            "Словарь исключений: более 200 слов с особым переводом",
            "Приставки бурмал-/бурмалд- добавляются к некоторым существительным",
            "Окончания -ость/-ность заменяют стандартные окончания существительных",
            "Глаголы, причастия и деепричастия не переводятся",
            "Служебные слова (предлоги, союзы, частицы) не переводятся",
            "Согласование прилагательных и местоимений с -ость/-ность словами",
            "Модели: -енье/-ение → -енность, -мя → -еность, -ица → -очность",
            "Модели: -ция → -чность, дорога → дорожность, машина → машинность",
            "Модели: наклейка → наклеичность, -ник → -ность, зонт → зонтичность",
            "Модель мягких существительных: поле → полесть",
            "Падежная модель для существительных на -у, -а, -я после предлогов",
        ],
        "examples": [
            {"ru": "Привет дорогой мой друг, как дела с твоим котом?", "burmalda": "Привет дорогой мок друн, как дела с твоей котостью?"},
            {"ru": "Меллстрой бурмалдит под зонтом.", "burmalda": "Меллстройность бурмалдит под зонтом."},
            {"ru": "Я помню чудное мгновенье.", "burmalda": "Ч помню чудною мгновенность."},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
