---

# ПОЛНЫЙ СПИСОК ВОПРОСОВ ДЛЯ ПОДГОТОВКИ

*Ориентироваться необходимо на эти темы. На зачете вопросы могут быть перефразированы.*

**Тема 1. Эволюция архитектур и OLTP vs OLAP**
1. Отличие OLTP от OLAP.
2. Для чего нужен Data Warehouse (DWH).
3. Для чего нужен Data Lake.
4. Отличие Data Lake от DWH.
5. Концепция Lakehouse.
6. Что такое MPP (Massively Parallel Processing).
7. Отличие Batch от Streaming обработки.
8. Плюсы и минусы Batch.
9. Плюсы и минусы Streaming.
10. Концепция Data Mesh.
11. Что такое Hadoop, какие особенности он имеет
12. Что такое S3, какие особенности он имеет
13. В чем отличие Hadoop и S3

**Тема 2. Компоненты платформы данных**
14. Что такое Data Platform.
15. Основные слои Data Platform (Sources, Ingestion, Storage, Processing, Serving).
16. Роль Ingestion.
17. Понятие Latency / Data freshness.
18. Роль слоя Storage.
19. Роль слоя Processing (ETL/ELT).
20. Роль слоя Serving.
21. Зачем нужен Metadata / Data Catalog.
22. Основы Security & Governance.
23. Основы Observability (Freshness, Quality, Availability).

**Тема 3. Архитектура данных в ритейле**
24. Основные бизнес-домены ритейла.
25. Что такое Master Data.
26. Проблема разных идентификаторов в системах.
27. Транзакционные данные vs Master Data.
28. Событийный слой (Events) в E-commerce.
29. Основные потребители данных (BI, Operations, ML).
30. Проблема Data Silos.
31. Проблема разной свежести данных (Freshness) в источниках.
32. Проблема разных бизнес-определений (Data Governance).

**Тема 4. Карта источников и Ingestion**
33. Что такое Source Map.
34. Типы источников данных (Database, Files, API, Events).
35. Отличие источника данных от базы данных.
36. Стратегия Full Load.
37. Стратегия Incremental Load.
38. Что такое CDC (Change Data Capture).
39. Проблема удаления данных (Deletes) при Incremental Load.
40. Проблема дублей при загрузке.
41. Понятие System of Record / Source of Truth.
42. Проблема нагрузки на Source System.

**Тема 5. Проектирование аналитической витрины**
43. Что такое Data Mart.
44. Понятие Grain (зерно фактовой таблицы).
45. Как определить Grain.
46. Отличие Fact от Dimension.
47. Типы Fact-таблиц (Transaction, Periodic Snapshot, Accumulating).
48. Схема Star Schema.
49. Схема Snowflake Schema.
50. Business Key vs Surrogate Key.
51. Additive, Semi-additive, Non-additive measures.
52. Ошибка Double Counting (смешение гранулярности).
53. Денормализация в аналитической модели.

**Тема 8. Проектирование ETL/ELT-потока**
54. Отличие ETL от ELT.
55. Роль Processing-компонента.
56. Этапы Data Pipeline.
57. Понятие Watermark.
58. Как и где хранится Watermark.
59. Главное правило обновления Watermark.
60. Понятие идемпотентности пайплайна.
61. Почему Retry не гарантирует корректность.
62. Проверки качества данных (Completeness, Uniqueness, Validity).
63. Роль Airflow в оркестрации.
64. Чего Airflow не делает.
65. Отличие Schedule Interval от Freshness.

**Тема 9. Бизнес-глоссарий и каталог данных**
66. Что такое Бизнес-глоссарий.
67. Что такое Каталог данных.
68. Отличие глоссария от каталога.
69. Роли (Data Owner, Data Steward, Data Engineer).
70. Data Lineage (происхождение данных).

---