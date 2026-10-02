Выбирайте задачу, которая соответствует вашему номеру в именном списке. **Список** прикреплен к **сообщению** об этом ДЗ в **канале**. 

Для всех задач целевая платформа одинаковая:

```text
Source → Ingestion → S3 → ClickHouse
```.

# Задача 1. ERP → товары

**Источник:** PostgreSQL ERP.
ERP является System of Record для товаров.

Таблица `products`:

| Поле          | Тип           | Описание              |
| ------------- | ------------- | --------------------- |
| `product_id`  | BIGINT PK     | ID товара             |
| `name`        | VARCHAR(500)  | Наименование          |
| `category_id` | BIGINT        | Категория             |
| `brand_id`    | BIGINT        | Бренд                 |
| `price`       | NUMERIC(12,2) | Цена                  |
| `status`      | VARCHAR(20)   | `ACTIVE` / `INACTIVE` |
| `updated_at`  | TIMESTAMP     | Последнее изменение   |

В таблице **5 млн строк**, около **20 тыс. строк изменяется в сутки**.

Новые товары добавляются через `INSERT`. При изменении товара обновляется `updated_at`. Удаление физически не выполняется: товар переводится в `status = INACTIVE`, при этом обновляется `updated_at`.

Доступ к PostgreSQL осуществляется через SQL. ERP — production-система; полное чтение таблицы разрешено не чаще одного раза в сутки.

Данные должны попадать в аналитическую платформу с задержкой **не более 1 часа**.

**Задание:** выбрать способ ingestion, определить SQL/механизм получения изменений, watermark, обработку повторной загрузки и сбоя, проверки качества и нарисовать архитектуру.

---

# Задача 2. ERP → цены

**Источник:** PostgreSQL ERP.
ERP является System of Record для цен.

Таблица `product_prices`:

| Поле         | Тип            | Описание            |
| ------------ | -------------- | ------------------- |
| `price_id`   | BIGINT PK      | ID записи           |
| `product_id` | BIGINT         | Товар               |
| `store_id`   | BIGINT         | Магазин             |
| `price`      | NUMERIC(12,2)  | Цена                |
| `valid_from` | TIMESTAMP      | Начало действия     |
| `valid_to`   | TIMESTAMP NULL | Конец действия      |
| `updated_at` | TIMESTAMP      | Последнее изменение |

В таблице **2 млн строк**, в сутки изменяется до **100 тыс. строк**.

Новые цены добавляются через `INSERT`. Исправление цены приводит к `UPDATE` и изменению `updated_at`. Исторические цены не удаляются физически. Запись становится неактивной через `valid_to`.

ERP предоставляет SQL-доступ. Полное чтение запрещено чаще одного раза в сутки.

Цена должна попадать в аналитическую платформу не позднее чем через **5 минут** после изменения.

**Задание:** выбрать ingestion, обосновать необходимость/ненужность CDC, определить обработку исторических версий цены и контроль задержки данных.

---

# Задача 3. ERP → поставщики

**Источник:** PostgreSQL ERP.
ERP — System of Record для поставщиков.

Таблица `suppliers`:

| Поле          | Тип          | Описание              |
| ------------- | ------------ | --------------------- |
| `supplier_id` | BIGINT PK    | ID поставщика         |
| `name`        | VARCHAR(300) | Название              |
| `inn`         | VARCHAR(20)  | ИНН                   |
| `status`      | VARCHAR(20)  | `ACTIVE` / `INACTIVE` |
| `region`      | VARCHAR(100) | Регион                |
| `updated_at`  | TIMESTAMP    | Изменение             |

В таблице **300 тыс. строк**. В среднем изменяется **2 тыс. строк в сутки**.

INSERT создаёт поставщика. UPDATE изменяет `updated_at`. DELETE не выполняется — используется `status = INACTIVE`.

Freshness — **не более 24 часов**.

Источник предоставляет SQL. Полный SELECT таблицы разрешён **один раз в сутки**.

**Задание:** спроектировать наиболее простой достаточный ingestion-процесс. Объяснить, почему более сложный механизм может быть неоправдан.

---

# Задача 4. POS → чеки

**Источник:** PostgreSQL POS.
POS является System of Record для факта продажи.

Таблица `receipts`:

| Поле           | Тип           |
| -------------- | ------------- |
| `receipt_id`   | BIGINT PK     |
| `store_id`     | BIGINT        |
| `cashier_id`   | BIGINT        |
| `customer_id`  | BIGINT NULL   |
| `total_amount` | NUMERIC(12,2) |
| `created_at`   | TIMESTAMP     |
| `updated_at`   | TIMESTAMP     |
| `status`       | VARCHAR(20)   |

В системе **200 млн чеков**, появляется около **5 млн новых чеков в сутки**.

Чек сначала создаётся со статусом `OPEN`, затем может перейти в `PAID` или `CANCELLED`. `updated_at` меняется при каждом изменении. Физический DELETE не используется.

Freshness — **не более 5 минут**.

POS является production-системой. Нельзя регулярно выполнять full scan.

**Задание:** выбрать ingestion, определить обработку `INSERT` и `UPDATE`, способ восстановления после сбоя и проверки полноты данных.

---

# Задача 5. POS → возвраты

**Источник:** PostgreSQL POS.

Таблица `returns`:

| Поле         | Тип           |
| ------------ | ------------- |
| `return_id`  | BIGINT PK     |
| `receipt_id` | BIGINT        |
| `product_id` | BIGINT        |
| `quantity`   | INT           |
| `amount`     | NUMERIC(12,2) |
| `reason`     | VARCHAR(100)  |
| `created_at` | TIMESTAMP     |
| `updated_at` | TIMESTAMP     |
| `status`     | VARCHAR(20)   |

В таблице **20 млн строк**, около **50 тыс. строк изменяется в сутки**.

Новая запись получает `status = CREATED`. Затем статус может измениться на `APPROVED` или `REJECTED`. DELETE не используется.

Freshness — **10 минут**.

Доступ только через SQL. Production POS нельзя нагружать запросами, читающими всю таблицу.

**Задание:** выбрать способ ingestion и определить, какие изменения необходимо передавать в аналитическую платформу.

---

# Задача 6. WMS → остатки

**Источник:** PostgreSQL WMS.
WMS — System of Record для складских остатков.

Таблица `stock`:

| Поле                | Тип           |
| ------------------- | ------------- |
| `warehouse_id`      | BIGINT        |
| `product_id`        | BIGINT        |
| `quantity`          | NUMERIC(14,3) |
| `reserved_quantity` | NUMERIC(14,3) |
| `updated_at`        | TIMESTAMP     |

PK:

```text
warehouse_id + product_id
```

В таблице **100 млн строк**. Остатки постоянно изменяются.

Freshness — **не более 1 минуты**.

WMS предоставляет SQL. Full scan production-базы запрещён.

**Задание:** спроектировать ingestion с учётом требования к freshness. Объяснить, почему выбранный механизм подходит для часто изменяющегося состояния.

---

# Задача 7. WMS → движения товара

**Источник:** PostgreSQL WMS.

Таблица `stock_movements`:

| Поле            | Тип           |
| --------------- | ------------- |
| `movement_id`   | BIGINT PK     |
| `warehouse_id`  | BIGINT        |
| `product_id`    | BIGINT        |
| `movement_type` | VARCHAR(30)   |
| `quantity`      | NUMERIC(14,3) |
| `created_at`    | TIMESTAMP     |
| `updated_at`    | TIMESTAMP     |

Типы движения:

```text
RECEIPT
SHIPMENT
TRANSFER
ADJUSTMENT
```

В таблице **500 млн записей**, около **2 млн новых записей в сутки**.

После создания движение обычно не изменяется. Отмена движения выполняется через отдельную запись `ADJUSTMENT`. DELETE не используется.

Freshness — **5 минут**.

**Задание:** выбрать способ загрузки и объяснить, почему для этой таблицы подход может отличаться от `stock`.

---

# Задача 8. WMS → поступления

**Источник:** PostgreSQL WMS.

Таблица `receipts`:

| Поле           | Тип            |
| -------------- | -------------- |
| `receipt_id`   | BIGINT PK      |
| `warehouse_id` | BIGINT         |
| `supplier_id`  | BIGINT         |
| `expected_at`  | TIMESTAMP      |
| `actual_at`    | TIMESTAMP NULL |
| `status`       | VARCHAR(20)    |
| `updated_at`   | TIMESTAMP      |

**30 млн строк**, около **100 тыс. изменений в сутки**.

Статусы:

```text
EXPECTED
RECEIVING
COMPLETED
CANCELLED
```

При изменении статуса обновляется `updated_at`. DELETE отсутствует.

Freshness — **1 час**.

SQL-доступ, full scan production запрещён чаще одного раза в сутки.

**Задание:** спроектировать ingestion и определить, достаточно ли incremental load.

---

# Задача 9. Loyalty → клиенты

**Источник:** PostgreSQL Loyalty.
Loyalty является System of Record для программы лояльности.

Таблица `customers`:

| Поле            | Тип          |
| --------------- | ------------ |
| `customer_id`   | BIGINT PK    |
| `phone`         | VARCHAR(30)  |
| `email`         | VARCHAR(200) |
| `birth_date`    | DATE NULL    |
| `loyalty_level` | VARCHAR(30)  |
| `status`        | VARCHAR(20)  |
| `updated_at`    | TIMESTAMP    |

**10 млн клиентов**, около **200 тыс. изменений в сутки**.

INSERT — регистрация клиента. UPDATE меняет `updated_at`. DELETE выполняется физически.

Freshness — **1 час**.

SQL-доступ. Полный scan production запрещён чаще одного раза в сутки.

**Задание:** выбрать ingestion с учётом необходимости корректно передавать физические DELETE.

---

# Задача 10. Loyalty → бонусные операции

**Источник:** PostgreSQL Loyalty.

Таблица `bonus_operations`:

| Поле             | Тип           |
| ---------------- | ------------- |
| `operation_id`   | BIGINT PK     |
| `customer_id`    | BIGINT        |
| `operation_type` | VARCHAR(30)   |
| `amount`         | NUMERIC(12,2) |
| `created_at`     | TIMESTAMP     |

Типы:

```text
ACCRUAL
SPEND
EXPIRE
CORRECTION
```

**500 млн записей**, около **3 млн новых операций в сутки**.

После создания запись не изменяется. DELETE запрещён.

Freshness — **5 минут**.

Доступ через SQL. Таблица находится в production.

**Задание:** определить наиболее подходящий способ ingestion для append-only данных и объяснить, нужен ли здесь CDC.

---

# Задача 11. E-commerce → заказы через API

E-commerce предоставляет **только REST API**.

Endpoint:

```text
GET /api/v1/orders
```

Параметры:

```text
updated_from
updated_to
page
page_size
```

Максимальный `page_size` — **100**.

API ограничивает клиента до **100 запросов в минуту**.

Ответ:

```json
{
  "order_id": 123,
  "customer_id": 456,
  "status": "PAID",
  "amount": 2500,
  "created_at": "...",
  "updated_at": "..."
}
```

**10 млн заказов**, около **100 тыс. изменений в сутки**.

Статусы:

```text
NEW
PAID
CANCELLED
DELIVERED
```

DELETE через API отсутствует. Заказы не удаляются.

Freshness — **15 минут**.

**Задание:** спроектировать API ingestion с учётом pagination, rate limit, watermark, retry и повторного запуска.

---

# Задача 12. E-commerce → каталог через API

API:

```text
GET /api/v1/products/changed
```

Возвращает товары, изменённые после указанного timestamp.

Максимум **1000 товаров за запрос**.

Товар:

```text
product_id
name
category_id
price
status
updated_at
```

Всего **500 тыс. товаров**, изменяется около **10 тыс. в сутки**.

API не поддерживает DELETE. Удалённый товар получает:

```text
status = INACTIVE
```

Freshness — **1 час**.

API доступен только в рабочие часы.

**Задание:** спроектировать ingestion, включая ситуацию, когда API недоступен ночью.

---

# Задача 13. E-commerce → статусы доставки

API:

```text
GET /api/v1/delivery/statuses
```

Максимум **100 записей за запрос**.

Для каждого заказа возвращается:

```text
order_id
status
updated_at
```

Статусы:

```text
CREATED
SHIPPED
IN_TRANSIT
DELIVERED
CANCELLED
```

Всего **20 млн заказов**.

Статусы могут изменяться несколько раз.

API не предоставляет CDC и не сообщает историю изменений — только **текущее состояние**.

Freshness — **10 минут**.

Есть ограничение **100 запросов/минуту**.

**Задание:** определить, возможно ли выполнить требование freshness при данных ограничениях API. Если невозможно — предложить архитектурный вариант решения.

---

# Задача 14. Mobile App → события пользователей

Мобильное приложение генерирует события:

```text
event_id
user_id
event_type
event_time
device_id
payload
```

Типы:

```text
APP_OPEN
PRODUCT_VIEW
ADD_TO_CART
REMOVE_FROM_CART
CHECKOUT
```

До **500 событий/секунду**.

События не изменяются после создания. DELETE отсутствует.

Требование freshness — **30 секунд**.

Приложение не предоставляет SQL или API для выгрузки событий. События могут доставляться в **RabbitMQ**.

**Задание:** спроектировать поток доставки событий через RabbitMQ в Data Platform. Определить, как обработать duplicate delivery и временную недоступность consumer.

---

# Задача 15. POS → события продаж

POS публикует события:

```text
event_id
receipt_id
event_type
event_time
store_id
amount
```

Типы:

```text
RECEIPT_CREATED
PAYMENT_COMPLETED
RECEIPT_CANCELLED
```

До **1000 событий/секунду**.

После публикации событие не изменяется.

Доставка возможна через **RabbitMQ**.

Freshness — **10 секунд**.

Возможна повторная доставка одного события.

**Задание:** спроектировать поток:

```text
POS → RabbitMQ → Consumer → S3 → ClickHouse
```

Определить:

* ключ дедупликации;
* поведение при падении consumer;
* подтверждение сообщения;
* контроль lag;
* контроль потери сообщений.

---

# Задача 16. Поставщик → CSV с товарами

Внешний поставщик ежедневно передаёт CSV-файл:

```text
product_id
name
category
brand
price
quantity
```

Файл появляется в S3 в **02:00**.

Размер — до **2 GB**, до **10 млн строк**.

Поставщик может прислать файл повторно. Имя файла:

```text
products_YYYYMMDD.csv
```

Иногда внутри файла встречаются дубли `product_id`.

Формат CSV фиксирован.

Freshness — **до 6 часов после появления файла**.

Файлы за прошлые даты не изменяются.

**Задание:** спроектировать batch ingestion. Обязательно определить:

* как определить, что файл уже обработан;
* как обнаружить дубли;
* как проверить полноту файла;
* что делать при появлении файла с ошибочной схемой.

---

# Задача 17. Поставщик → закупочные цены

Поставщик передаёт CSV:

```text
product_id
supplier_id
price
currency
valid_from
```

Файл приходит **раз в сутки**.

Размер — до **10 млн строк**.

Один и тот же файл может быть отправлен повторно. Иногда поставщик присылает исправленный файл за предыдущую дату.

Файл может содержать несколько записей для одного:

```text
product_id + supplier_id
```

с разными `valid_from`.

Freshness — **24 часа**.

Файлы поступают в S3.

**Задание:** разработать batch ingestion с идемпотентностью и обработкой повторной поставки/исправления исторического файла.

---

# Задача 18. ERP → исторические заказы

ERP содержит:

```text
orders
----------------
order_id BIGINT PK
customer_id BIGINT
amount NUMERIC(12,2)
status VARCHAR(20)
created_at TIMESTAMP
updated_at TIMESTAMP
```

Объём — **2 млрд записей**.

Ежедневно появляется около **100 тыс. новых заказов**.

Заказы могут изменять статус. DELETE не выполняется.

Freshness новых изменений — **1 час**.

ERP предоставляет SQL-доступ.

Полный extraction всех 2 млрд записей за один запуск невозможен.

**Задание:** спроектировать **двухэтапную стратегию**:

```text
Historical Load
       +
Regular Incremental Load
```

Необходимо определить:

* как разбить историческую загрузку;
* как не потерять данные, появившиеся во время initial load;
* как после initial load перейти на регулярную загрузку;
* как определить момент готовности исторического слоя.

---

# Задача 19. CRM → клиенты и контакты

CRM работает на PostgreSQL.

Таблица `customers`:

| Поле          | Тип          |
| ------------- | ------------ |
| `customer_id` | BIGINT PK    |
| `name`        | VARCHAR(300) |
| `phone`       | VARCHAR(30)  |
| `email`       | VARCHAR(200) |
| `segment`     | VARCHAR(50)  |
| `status`      | VARCHAR(20)  |
| `updated_at`  | TIMESTAMP    |

**30 млн записей**.

В сутки:

* ~100 тыс. INSERT;
* ~300 тыс. UPDATE;
* ~10 тыс. DELETE.

При UPDATE изменяется `updated_at`.

DELETE выполняется **физически**, дополнительного признака удаления нет.

Freshness — **15 минут**.

CRM — production-система. Full scan запрещён.

Доступен SQL.

**Задание:** спроектировать ingestion, который гарантированно учитывает **INSERT, UPDATE и DELETE**. Отдельно объяснить, почему простой запрос вида

```sql
WHERE updated_at > :watermark
```

не решает задачу полностью.

---