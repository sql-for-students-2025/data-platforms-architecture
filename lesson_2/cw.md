# Занятие 2. Компоненты современной платформы данных

После прошлого раза мы знаем, **почему архитектуры эволюционировали**. Теперь нужно показать, **из каких блоков состоит современная Data Platform и как данные проходят через неё**.

### Главный вопрос занятия

> **Что происходит с данными от момента их появления в бизнес-системе до момента, когда аналитик использует их для принятия решения?**

---

## 1. Вспоминаем прошлое занятие

Два вопроса:

1. Почему нельзя просто использовать PostgreSQL для всего?
2. Почему Data Lake сам по себе ещё не является полноценной Data Platform?

Вывод:

> Нам нужны не только storage и database. Нужна **система компонентов, которая обеспечивает полный жизненный цикл данных**.

---

# 2. Что такое Data Platform

Дать определение:

> **Data Platform — совокупность технологий, процессов и правил, обеспечивающих сбор, хранение, обработку, управление и предоставление данных потребителям.**

Важно:

**Data Platform ≠ Data Warehouse.**

DWH — один из компонентов.

Показать:

```text
                    DATA PLATFORM

 Sources → Ingestion → Storage → Processing → Serving → Consumers
                                      │
                           ┌──────────┼──────────┐
                           ▼          ▼          ▼
                        Metadata   Security   Monitoring
```

---

# 3. Полный путь данных

Это **главная схема всего занятия**.

```text 
┌──────────┐
│ Sources  │
└────┬─────┘
     │
     ▼
┌──────────┐
│Ingestion │
└────┬─────┘
     │
     ▼
┌──────────┐
│ Storage  │
└────┬─────┘
     │
     ▼
┌──────────┐
│Transform │
└────┬─────┘
     │
     ▼
┌──────────┐
│ Serving  │
└────┬─────┘
     │
     ▼
┌──────────┐
│ BI / ML  │
└──────────┘
```

А вокруг:

```text
        Metadata / Catalog
        Data Quality
        Security
        Governance
        Observability
```

Объяснить:

> **Данные движутся по pipeline, а metadata, security, quality и observability должны сопровождать их на всём пути.**

---

# 4. Sources 

Начинаем с источников.

Для ритейла:

```text 
ERP ──────────┐
POS ──────────┤
WMS ──────────┤
E-commerce ───┤
Mobile App ───┤──► Data Platform
Loyalty ──────┤
CRM ──────────┘
```

Разделить источники на:

### Operational

* PostgreSQL;
* ERP;
* CRM;
* WMS;
* POS.

### Events

* клики;
* покупки;
* изменения статусов;
* мобильные события.

### Files

* CSV;
* Excel;
* JSON;
* внешние выгрузки.

### External

* курсы валют;
* погода;
* маркетплейсы;
* поставщики.

---

## Важная мысль

Источник данных выбирается **не data engineer'ом**.

Источник возникает потому, что **бизнес-процесс породил систему**.

Например:

> WMS существует для управления складом, а не для аналитики.

Поэтому аналитическая платформа должна **забирать данные из operational systems**, не ломая их основную работу.

---

# 5. Ingestion 

**Ingestion = доставка данных из источника на платформу.**

Две модели:

### Batch

```text 
PostgreSQL
    │
    │ каждые 60 минут
    ▼
  Airflow
    │
    ▼
   S3
```

### Streaming

```text
POS
 │
 ▼
RabbitMQ
 │
 ▼
Consumer
 │
 ▼
Platform
```

Определим термин:

> **Latency / data freshness**

Например:

```text
Report freshness < 24 h
Report freshness < 1 h
Report freshness < 5 min
Report freshness < 1 sec
```

**Архитектура ingestion определяется прежде всего требованием к свежести данных.**

---

# 6. Storage 

Теперь вопрос:

> Куда складываем данные?

Разделяем роли.

### PostgreSQL

```text
OLTP
transactions
current state
```

### S3

```text
Data Lake
raw files
historical data
large objects
```

### ClickHouse

```text
OLAP
analytical queries
aggregations
data marts
```

### Redis

```text
fast access
cache
hot data
operational serving
```

Главная мысль:

> **Одна технология хранения не обязана решать все задачи.**

---

# 7. Processing: ETL vs ELT

Очень важный блок.

### ETL

```text
Source
  │
  ▼
Extract
  │
  ▼
Transform
  │
  ▼
Load
  │
  ▼
DWH
```

### ELT

```text
Source
  │
  ▼
Extract
  │
  ▼
Load
  │
  ▼
DWH / Lake
  │
  ▼
Transform
```

Пример:

```text
PostgreSQL
     │
     ▼
    S3
     │
     ▼
ClickHouse
     │
     ▼
transformations
```

Возникает вопрос:

**Когда трансформировать?**

Ответ:

> Зависит от возможностей storage/compute, требований к raw data, governance и конкретной архитектуры.

---

# 8. Serving layer

После обработки данные должны **кому-то предоставляться**.

```text 
                  Data Platform
                       │
                 ┌─────┴─────┐
                 ▼           ▼
            ClickHouse     Redis
                 │           │
                 ▼           ▼
                BI          API
```

Например:

### ClickHouse

> «Продажи по магазинам за 3 года».

### Redis

> «Топ-10 товаров магазина прямо сейчас».

### BI

> «Дашборд директора».

---

# 9. Metadata / Catalog / Lineage 

Данные без контекста быстро превращаются в проблему.

Допустим, аналитик видит:

```text
sales.amount
```

Вопросы:

* Что такое amount?
* С НДС или без?
* В какой валюте?
* Кто владелец?
* Как рассчитывается?
* Когда обновляется?
* Из какого источника пришло?

Поэтому появляются:

### Data Catalog

> Какие данные у нас есть?

### Metadata

> Что мы знаем об этих данных?

### Lineage

> Откуда эти данные пришли и куда попали?

Схема:

```text 
PostgreSQL
    │
    ▼
orders
    │
    ▼
ETL
    │
    ▼
fact_sales
    │
    ▼
BI dashboard
```

Это и есть lineage.

---

# 10. Security & Governance 

Вопрос:

> Можно ли дать всем аналитикам доступ ко всем данным?

Очевидно, нет.

Появляются:

* authentication;
* authorization;
* RBAC;
* data classification;
* PII;
* audit;
* encryption.

Пример:

```text 
Customer
  │
  ├── name             → restricted
  ├── email            → restricted
  ├── customer_id      → internal
  └── sales_amount     → analytics
```

И важный принцип:

> **Безопасность — не отдельный этап после построения платформы. Она должна проходить через всю платформу.**

---

# 11. Observability

Последний слой:

> **Как понять, что наша платформа работает правильно?**

Не только используя показатели железа:

```text 
CPU = 70%
RAM = 60%
```

Но и показатели работы пайплайна и других компонентов:

```text
Pipeline:
 - DAG completed
 - 1.2M records loaded
 - freshness = 7 min
 - quality = 99.8%

RabbitMQ:
 - queue depth = 120

ClickHouse:
 - query latency = 300 ms
```

А следующие показатели удовлетворяют допустимым значениям:

### Freshness

Насколько свежи данные?

### Quality

Насколько данные корректны?

### Availability

Доступна ли система?

---

# Итог занятия


```text
                       DATA PLATFORM

 SOURCES
    │
    ▼
INGESTION ────────► BATCH / STREAMING
    │
    ▼
 STORAGE ─────────► PostgreSQL / S3 / ClickHouse / Redis
    │
    ▼
PROCESSING ───────► ETL / ELT
    │
    ▼
 SERVING ─────────► Data Marts / API / BI
    │
    ▼
 CONSUMERS ───────► Analysts / Business / ML


 ──────────────────────────────────────────────
 Metadata | Catalog | Lineage | Quality
 Security | Governance | Observability
 ──────────────────────────────────────────────
```

### Главная мысль занятия

> **Современная Data Platform — это не одна база данных. Это цепочка компонентов, каждый из которых решает свою часть задачи, объединённая общими правилами управления данными.**

