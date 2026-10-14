### Задание: «Спроектировать аналитическую витрину»

Необходимо выбрать один сценарий:

* продажи;
* остатки;
* возвраты;
* заказы e-commerce;
* loyalty;
* поставки;
* движение товара;
* эффективность магазинов;
* доставка;
* мобильные события.

и предоставить **витрину**:

### 1. Business questions

Минимум 3 вопроса, на которые должна отвечать витрина.

### 2. Grain

Одно точное предложение:

> Одна строка представляет ...

### 3. Fact

* название;
* ключи;
* 4–6 measures.

### 4. Dimensions

Минимум 3 измерения.

### 5. Schema

Star schema в виде простой диаграммы.

### 6. Aggregation rules

Для каждого основного measure:

```text
SUM / AVG / COUNT / not additive
```

и краткое объяснение.

### 7. Один риск

Например:

* double counting;
* changing dimensions;
* duplicate events;
* inconsistent business definition;
* wrong grain.
