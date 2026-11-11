### Необходимо переписать ваш консьюмер таким образом, чтоб он писал файлы в S3, а потом данные забирались с помощью Clickhouse. 

**Учтите, что писать в S3 можно только из Airflow.**

План действий:
1. Создать тестовый даг на основе того, что описан в `cw.md`. Инструкция как правильно сложить файлы [здесь](https://github.com/sql-for-students-2025/airflow_dags_for_courses/blob/main/airflow_dags/students_dags/Readme.md)
2. Протестировать его запуск. 
3. Создать на Clickhouse ваши таблицы справочников и фактов. Учтите, что Clickhouse имеет свои особенности как в типах данных, так и при создании таблиц. Подробнее можете изучить в [документации](https://clickhouse.com/docs/reference/syntax)
4. Создать даг для своего ETL/ELT-потока. 
    - в тегах обязательно указываем свой логин и номер ДЗ, чтоб по ним можно было фильтровать
    - **ни в коем случае** не указываем никаких чувствительных данных в коде дага. Логин и пароль для RabbitMQ необходимо использовать сервисные. Их получение показано в коде ниже. 
    - Все исполняющие функции вынести в подпапку `subtask_scripts`. 
    - В файле должно присутствовать 2 функции (получение данных из RabbitMQ и запись данных в S3 (данные писать в каталог DATA/your_login/), заливка данных из S3 в Clickhouse)
    - Для каждой функции должна быть отдельная задача в даге. 
5. Протестировать запуск дага.

---

Чтоб не светить в коде ключи необходимо использовать их получение через переменные

```python

from airflow.models import Variable

access_key = Variable.get('s3_dad_ksu_dataplatform_access_key')
secret_key = Variable.get('s3_dad_ksu_dataplatform_secret_key')
rabbitmq_svc_password = Variable.get('rabbit_mq_svc_password')
rabbit_mq_svc_login = Variable.get('rabbit_mq_svc_login')
rabbit_mq_host = Variable.get('rabbit_mq_host')
clickhouse_svc_login = Variable.get('clickhouse_tech_user_account')
clickhouse_svc_password = Variable.get('clickhouse_tech_user_password')
clickhouse_host = Variable.get('clickhouse_port')

```

Пример создания подключения к Clickhouse с помощью библиотеки clickhouse-driver

```python
from clickhouse_driver.client import Client

# если будете использовать pandas, то эта настройка поможет избежать ошибок
settings = {
    'use_numpy': True
}

with Client(
    host=clickhouse_host, 
    гser=clickhouse_svc_login, 
    password=clickhouse_svc_password, 
    database='<your_login>_db'
    settings=settings, #если pandas не используете можно удалить этот параметр
    port=9000
    ) as client:

    client.execute(sql="select 1;")
```

Пример создания таблицы на Clickhouse

```sql

drop table if exists <your_login>_db.test;
create table <your_login>_db.test (
	id UInt8,
	name String
)
engine=MergeTree --используем этот движок
order by id; --как правило сортируем по уникальному ключу, в сортировке может участвовать несколько полей

```