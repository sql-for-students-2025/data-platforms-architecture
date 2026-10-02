# Единый шаблон ответа студента

### 1. Source Profile

```text
Source:
Domain:
System of Record:
Interface:
Volume:
Change rate:
Freshness:
```

### 2. Архитектурное решение

```text
Source
  ↓
Interface
  ↓
Ingestion method
  ↓
S3
  ↓
ClickHouse
```

### 3. Почему выбран именно этот ingestion

**1–2 тезиса.**

### 4. Работа с изменениями

* INSERT
* UPDATE
* DELETE

### 5. Надёжность

* retry;
* duplicate;
* failure recovery;
* watermark / offset.

### 6. Data Quality

Минимум **3 проверки**.

### 7. Мониторинг

Минимум **3 метрики/алерта**.

Например:

```text
pipeline success/failure
freshness
records processed
source-target count
lag
duplicate rate
```
