# Занятие 5. Проектирование аналитической витрины

---

## 1. Цель занятия

После занятия студент должен уметь:

* определить **зерно (grain)** фактовой таблицы;
* отличать **факты от измерений**;
* выбирать измерения и показатели;
* понимать разницу между **natural/business key** и surrogate key;
* проектировать простую **звезду (star schema)**;
* избегать типичных ошибок при проектировании витрин;
* объяснять, почему выбранная гранулярность подходит для конкретного сценария.

Главная мысль занятия:

> **Хорошая аналитическая витрина начинается не с таблиц, а с вопроса: что именно мы хотим измерять и на каком уровне детализации?**

---

# 2. Связь с предыдущими занятиями

> **Как из всей платформы получить конкретный набор данных, удобный для аналитика/BI.**

Например:

```text
POS / ERP / WMS
      ↓
   Ingestion
      ↓
 S3 / Processing
      ↓
   ClickHouse
      ↓
 sales_mart
      ↓
     BI
```

До этого мы проектировали **платформу**.

Теперь проектируем **одну витрину внутри неё**.

---

# 3. Что такое аналитическая витрина

Аналитическая витрина (**Data Mart**) — это набор данных, подготовленный под конкретный аналитический сценарий или группу связанных сценариев.

Например:

* продажи;
* остатки;
* клиенты;
* заказы e-commerce;
* эффективность магазинов;
* продажи по товарам.

Витрина должна быть:

* понятной;
* стабильной;
* удобной для аналитических запросов;
* согласованной с бизнес-определениями;

Важно:

> Витрина — не просто «таблица, которую построили для BI».

Это **модель данных**, в которой заранее определены сущности, связи, гранулярность и показатели.

---

# 4. Почему нельзя начинать с таблиц

Типичная ошибка студента:

> «Нам нужны продажи → создадим таблицу `sales` и положим туда всё».

В результате появляется:

```text
sales
--------------------------------
order_id
customer_name
customer_phone
product_name
category_name
store_name
city
manager_name
quantity
price
discount
...
```

Проблемы:

* повторение данных;
* сложные изменения;
* неясная гранулярность;
* смешение разных сущностей;
* риск двойного подсчёта;
* трудно понять, что означает одна строка.

Поэтому первый вопрос:

> **Что означает одна строка фактовой таблицы?**

Это и есть **grain**.

---

# 5. Grain — зерно фактовой таблицы

**Grain** — уровень детализации, на котором существует одна строка факта.

Например:

### Вариант 1

Одна строка = одна продажа товара в чеке.

```text
receipt_id | product_id | quantity | amount
```

Тогда:

> grain = одна линия в чеке

### Вариант 2

Одна строка = один чек.

```text
receipt_id | store_id | customer_id | total_amount
```

Тогда:

> grain = один чек

### Вариант 3

Одна строка = продажи товара за день в магазине.

```text
date | store_id | product_id | quantity | amount
```

Тогда:

> grain = один продукт × магазн × день

---

## Почему grain настолько важен

Предположим:

```text
Чек 1001
---------------------
Milk     2 × 100 = 200
Bread    1 ×  80 =  80
```

Если таблица имеет grain:

> одна строка = товарная позиция чека

то будет:

```text
receipt_id | product | qty | amount
1001       | Milk    | 2   | 200
1001       | Bread   | 1   | 80
```

Если аналитик посчитает:

```sql
SELECT receipt_id, SUM(amount) FROM sales GROUP BY receipt_id;
```

получит 280.

Если же мы смешаем в одной строке одновременно данные чека и товара, легко получить двойной подсчёт.

---

# 6. Как определить grain

Полезный шаблон для студентов:

> **Одна строка это ...**

Например:

> Одна строка представляет собой продажу одного продукта в одном чеке.

или:

> Одна строка представляет хранение одного продукта на одном складе в определенную точку времени.

---

# 7. Fact и Dimension

Классическая аналитическая модель состоит из:

* **Fact** — факты/события, которые мы измеряем;
* **Dimension** — контекст, в котором мы их анализируем.

Например, продажи:

```text
             dim_date
                |
dim_product — fact_sales — dim_store
                |
           dim_customer
```

---

# 8. Fact table

Фактовая таблица обычно содержит:

* ссылки на измерения (ID);
* числовые показатели;
* иногда технические поля.

Пример:

```text
fact_sales
-------------------------
date_key
product_key
store_key
customer_key
receipt_id
quantity
gross_amount
discount_amount
net_amount
```

Здесь:

* `quantity` — сколько продали;
* `gross_amount` — сумма до скидки;
* `discount_amount` — скидка;
* `net_amount` — итоговая сумма.

---

# 9. Dimension table

Измерения отвечают на вопрос:

> **В каком контексте мы анализируем факт?**

Например:

```text
dim_product
-------------------------
product_key
product_id
product_name
brand
category
subcategory
```

```text
dim_store
-------------------------
store_key
store_id
store_name
city
region
format
```

```text
dim_date
-------------------------
date_key
date
day
month
quarter
year
weekday
```

---

# 10. Пример аналитического запроса

Бизнес-вопрос:

> Сколько мы продали молока в магазинах Варшавы в сентябре?

Факты:

```text
fact_sales
```

Измерения:

```text
dim_product
dim_store
dim_date
```

Запрос концептуально выглядит так:

```sql
SELECT
    p.category,
    s.city,
    d.month,
    SUM(f.net_amount) AS revenue
FROM fact_sales f
JOIN dim_product p
    ON f.product_key = p.product_key
JOIN dim_store s
    ON f.store_key = s.store_key
JOIN dim_date d
    ON f.date_key = d.date_key
WHERE
    s.city = 'Warsaw'
    AND d.month = 9
GROUP BY
    p.category,
    s.city,
    d.month;
```

Важно не запоминать SQL.

Нужно понимать модель:

```text
FACT
 ↓
measure
 ↓
DIMENSIONS
 ↓
analysis
```

---

# 11. Star Schema

Классическая модель для аналитической витрины:

```text
                 dim_date
                    |
                    |
dim_product ---- fact_sales ---- dim_store
                    |
                    |
               dim_customer
```

Это **звезда**.

Центр:

```text
fact_sales
```

Вокруг:

```text
dimensions
```

---

# 12. Почему Star Schema удобна

Она:

* проста для понимания;
* хорошо соответствует аналитическим запросам;
* удобна для BI;
* позволяет независимо анализировать факты по разным измерениям;
* уменьшает количество сложных связей для аналитика.

Например:

```text
Продажи
  ↓
по времени
по магазинам
по товарам
по клиентам
```

---

# 13. Факты бывают не только «продажами»

Это важный момент.

### Transaction fact

Каждая транзакция:

```text
sale
order
payment
return
```

### Periodic snapshot

Состояние на определённый момент/период.

Например:

```text
stock_daily
```

```text
date | warehouse | product | quantity
```

### Accumulating snapshot

Жизненный цикл процесса.

Например, заказ:

```text
order_created
payment
packing
shipment
delivery
```

Одна строка может постепенно отражать прохождение заказа по этапам.

---

# 14. Пример: витрина остатков

Здесь нельзя просто взять модель продаж.

Вопрос:

> Что означает одна строка?

Вариант:

> Одна строка представляет запасы одного товара на одном складе на конец дня.

Тогда:

```text
fact_stock_daily
-------------------------
date_key
warehouse_key
product_key
stock_qty
stock_value
```

Измерения:

```text
dim_date
dim_warehouse
dim_product
```

Схема:

```text
               dim_date
                   |
                   |
dim_product -- fact_stock_daily -- dim_warehouse
```

---

# 15. Самая важная ошибка: смешивание фактов

Предположим, есть:

```text
fact_sales
fact_stock
fact_returns
```

Не стоит бездумно объединять их в:

```text
fact_everything
```

Почему?

У них разные:

* grain;
* события;
* показатели;
* временная семантика.

Например:

```text
fact_sales
grain = product × receipt

fact_stock_daily
grain = product × warehouse × day

fact_returns
grain = returned item
```

Это разные факты.

---

# 16. Grain важнее названия таблицы

Очень полезно дать студентам этот пример.

Таблица называется:

```text
sales
```

Но что означает строка?

Возможны варианты:

```text
1 row = receipt
```

или

```text
1 row = receipt line
```

или

```text
1 row = product × store × day
```

Все три могут называться `sales`.

Поэтому название таблицы **не определяет её семантику**.

---

# 17. Measures — показатели

Measures — числовые значения, которые обычно агрегируются.

Примеры:

```text
quantity
revenue
discount
cost
margin
```

Но важно разделять:

### Additive

Можно складывать по всем измерениям.

```text
quantity
revenue
cost
```

### Semi-additive

Можно складывать по некоторым измерениям, но нельзя по другим.

Классический пример:

```text
stock_quantity
```

Можно сложить:

```text
stock разных складов
```

Но нельзя просто сложить:

```text
stock на 1 января
+
stock на 2 января
```

Получится бессмысленно.

### Non-additive

Например:

```text
margin_percent
conversion_rate
```

Их нельзя корректно суммировать.

---

# 18. Derived measures

Не все показатели обязательно хранить.

Например:

```text
revenue = quantity × price
```

Можно вычислять.

Но иногда бизнес-логика сложнее:

```text
net_revenue
```

может зависеть от:

* скидок;
* возвратов;
* налогов;
* корректировок.

Тогда нужно явно определить бизнес-правило.

Главная идея:

> **Показатель должен иметь однозначное бизнес-определение.**

---

# 19. Keys

В витринах нужно различать два типа ключей.

### Business / Natural Key

Ключ из исходной системы:

```text
product_id = 12345
store_id = 17
customer_id = 987654
```

Он идентифицирует сущность в бизнес-системе.

### Surrogate Key

Технический ключ внутри аналитической модели:

```text
product_key = 100234
```

Он используется как ключ измерения.

---

# 20. Зачем surrogate key

Особенно важно при изменении измерений.

Например, товар:

```text
product_id = 123
category = "Milk"
```

Через полгода товар перевели в другую категорию.

Если нам нужно хранить историю:

```text
2025 → Milk
2026 → Dairy
```

аналитическая модель должна уметь различать эти версии.

---

# 21. Денормализация

В OLTP часто стремятся к нормализации.

В аналитической модели допустима денормализация.

Например, вместо:

```text
product
  ↓
category
  ↓
department
```

можно сделать:

```text
dim_product
--------------------------------
product
category
subcategory
department
brand
```

Почему?

Потому что аналитические запросы часто должны быть простыми и быстрыми.

Но:

> Денормализация не означает «складываем всё в одну огромную таблицу».

---

# 22. Star vs Snowflake

Можно кратко показать альтернативу.

### Star

```text
             category
                ↑
product ← fact → store
                ↑
               date
```

или, если category находится внутри product:

```text
product
   \
    fact
   /   \
store  date
```

### Snowflake

Измерения дополнительно нормализованы:

```text
fact
 |
product
 |
category
 |
department
```

> **Star обычно проще для BI и обучения; Snowflake может уменьшить дублирование, но делает модель сложнее.**

---

# 23. Важная проблема: разные grain

Рассмотрим заказ:

```text
order_id = 100
```

В нём:

```text
Product A — 2
Product B — 1
Product C — 5
```

Если сделать:

```text
fact_order
```

и одновременно хранить:

```text
order total
product
quantity
```

возникает проблема.

`order_total = 1000` будет повторяться для каждой товарной строки.

Если сделать:

```sql
SUM(order_total)
```

получим:

```text
3000
```

вместо:

```text
1000
```

Это классическая ошибка **double counting**.

---

# 24. Практика на занятии

## Кейс: Sales Mart

Ритейлер хочет аналитическую витрину продаж.

Есть источники:

### POS

```text
receipt_id
store_id
customer_id
sale_time
status
```

### POS receipt lines

```text
receipt_id
product_id
quantity
unit_price
discount
```

### Product

```text
product_id
product_name
category
brand
```

### Store

```text
store_id
store_name
city
region
```

Бизнес хочет отвечать на вопросы:

1. Сколько продали товара?
2. Выручка по магазинам?
3. Продажи по категориям?
4. Продажи по дням?
5. Продажи по клиентам?
6. Средний чек?
7. Топ товаров?

---

Cпроектировать `sales_mart`.

Обязательно определить:

### 1. Grain

Одно предложение:

> One row represents ...

### 2. Fact table

Определить:

* название;
* ключи;
* measures.

### 3. Dimensions

Минимум:

* Date;
* Product;
* Store.

Дополнительно:

* Customer.

### 4. Measures

Например:

```text
quantity
gross_amount
discount_amount
net_amount
```

### 5. Business keys / surrogate keys

Определить, какие ключи использовать.

### 6. Два бизнес-запроса

Показать, как модель отвечает на:

> Revenue by store and month

и

> Top 10 products by revenue.

---

# Результат

Например:

```text
                    dim_date
                       |
                       |
dim_product ------ fact_sales ------ dim_store
                       |
                       |
                  dim_customer
```

### fact_sales

```text
sales_key
date_key
product_key
store_key
customer_key
receipt_id

quantity
gross_amount
discount_amount
net_amount
```

### dim_product

```text
product_key
product_id
product_name
brand
category
```

### dim_store

```text
store_key
store_id
store_name
city
region
```

### dim_date

```text
date_key
date
day
month
quarter
year
```

---

# 25. Типичные ошибки 

### Ошибка 1. Нет grain

```text
fact_sales
```

и дальше сразу список колонок.

**Исправление:** сначала `one row represents...`.

---

### Ошибка 2. Факт = всё подряд

```text
customer_name
product_name
store_name
category
revenue
city
manager
...
```

**Исправление:** отделить dimensions.

---

### Ошибка 3. Смешение разных grain

```text
order total
+
order line
```

**Результат:** double counting.

---

### Ошибка 4. Всё считать dimensions

Например:

```text
revenue
quantity
discount
```

как атрибуты продукта.

**Исправление:** определить, что измеряется в факте.

---

### Ошибка 5. Суммировать то, что нельзя суммировать

Например:

```text
AVG(margin_percent)
SUM(stock_by_day)
```

без понимания семантики.

---

### Ошибка 6. Делать одну универсальную таблицу

```text
sales_stock_orders_customers
```

Это почти всегда признак отсутствия модели.

---

# 26. Итоговая схема занятия

> **Business question → Grain → Fact → Dimensions → Measures → Analytical queries**