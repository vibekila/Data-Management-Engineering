# Data Management Engineering

Учебный проект по инжинирингу данных: загрузка и подготовка датасета, исследовательский анализ, работа с открытым API и запись данных в PostgreSQL.

## Датасет

Используется датасет результатов плетизмографии самцов мышей линии CD1 (показатели дыхания). Исходная таблица содержит около 1000 записей и 15 признаков.

Источник: [dataset_for_DME (Google Sheets)](https://docs.google.com/spreadsheets/d/1op5pVvniPLiL88I-HxvgWKKqM0AA2PsP/edit).

## Структура проекта

```text
Data-Management-Engineering/
├── data/                       # Локальные данные
├── notebooks/
│   └── EDA.ipynb               # Исследовательский анализ данных
├── scripts/
│   ├── read_api.py             # Запросы к GBIF API
│   ├── write_to_db.py          # Загрузка 100 строк в PostgreSQL
│   ├── beetles_api.png
│   └── README.md               # Инструкция для read_api.py
├── data_loader.py              # Загрузка датасета и преобразование типов
├── requirements.txt
├── .gitignore
└── README.md
```

Папка `data/` создаётся локально и исключена из Git. Она содержит исходный CSV, обработанный Parquet и файл реквизитов `creds.db`.

## Установка

Из корня проекта:

```bash
python -m pip install -r requirements.txt
```

## Загрузка и подготовка данных

```bash
python data_loader.py
```

Скрипт `data_loader.py`:

1. Использует локальный `data/dataset_for_DME.parquet`, если он существует.
2. Иначе читает `data/dataset_for_DME.csv`, при отсутствии CSV скачивает его из Google Sheets.
3. Приводит числовые признаки к числовым типам и сохраняет результат в `data/dataset_for_DME.parquet`.
4. Выводит первые 10 строк.

## Исследовательский анализ данных

В `notebooks/EDA.ipynb` выполнен исследовательский анализ датасета. Для работы с ноутбуком откройте его в VS Code или Jupyter с установленными зависимостями.

## Работа с открытым API

Скрипт `scripts/read_api.py` получает данные о находках жуков (Coleoptera) из GBIF API.

```bash
python scripts/read_api.py
```

Дополнительная информация и пример вывода находятся в `scripts/README.md`.

## Запись в PostgreSQL

Скрипт `scripts/write_to_db.py` переносит **первые 100 строк** из `data/dataset_for_DME.parquet` в PostgreSQL, в таблицу `giniyatullinadm` базы `homeworks`.

Этапы работы:

1. `load_dataset()` — читает Parquet и выбирает первые 100 строк.
2. `load_credentials()` — получает параметры подключения из локальной SQLite-базы `data/creds.db`, таблица `access`.
3. `connect_to_db()` — подключается к PostgreSQL через `psycopg2`.
4. `prepare_columns()` — преобразует имена столбцов для SQL и подбирает типы `DOUBLE PRECISION` или `TEXT`.
5. `write_dataframe()` — пересоздаёт таблицу, записывает строки через `executemany()` и подтверждает транзакцию (`commit`). При ошибке выполняется `rollback`.

**Подготовка:** сначала создайте Parquet командой `python data_loader.py` (если он отсутствует). Затем разместите `creds.db` в папке `data/`. Файл реквизитов базы данных не входит в репозиторий.

**Запуск:**

```bash
python scripts/write_to_db.py
```

При каждом запуске скрипт выполняет `DROP TABLE IF EXISTS` для таблицы `giniyatullinadm` и создаёт её заново. Не запускайте повторно, если содержимое существующей таблицы нужно сохранить.