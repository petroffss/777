# PDF Contract Analyzer

Инструмент для рекурсивного поиска PDF-договоров, извлечения текста (с OCR при необходимости) и анализа ключевых полей через LLM. Результат формируется в Excel или CSV.

## Установка

```bash
pip install -r requirements.txt
```

Создайте `.env` на основе `.env.example` и укажите ключи:

```bash
cp .env.example .env
```

## Запуск

```bash
python main.py --directory /path/to/contracts --api gemini --output results.xlsx
```

### Опции

- `--directory / -d` — директория для поиска PDF (обязательный)
- `--api` — `gemini` или `openrouter` (по умолчанию gemini)
- `--output / -o` — путь для отчета (по умолчанию авто)
- `--max-pages` — максимум страниц для анализа (по умолчанию 5)
- `--output-format` — `xlsx` или `csv` (по умолчанию xlsx)
- `--ocr` — `on`, `off` или `auto` (по умолчанию auto)
- `--max-chars` — ограничение символов для LLM (по умолчанию 20000)
- `--verbose / -v` — подробный лог

## Пример

```bash
python main.py -d ./contracts --api openrouter --output-format csv --ocr auto
```

## Примечания

- OCR требует установленного Tesseract и Poppler.
- Ошибки логируются в `errors.log`.
- Кэш результатов хранится в `.cache/contracts_cache.json`.
