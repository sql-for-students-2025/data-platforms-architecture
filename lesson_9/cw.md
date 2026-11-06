### Параметры для подключения к БД Clickhouse

IP - `111.88.243.32`
PORT - `8123`
DATABASE - `<your_login>_db` 
Логин и пароль выданы вам ранее. 

---
### Вставка данных в файл S3 с помощью Clickhouse можно осуществлять с помощью следующего запроса

```sql
INSERT INTO FUNCTION s3( 
	'https://storage.yandexcloud.net/dad-ksu-datalab/DATA/test_file.parquet', --здесь указываем полный путь к файлу, если подкаталога (DATA) 
    --и файла test_file.parquet' не существует, то они будут созданы автоматически
    'ACCESS_KEY', --не забудьте поменять на настоящие, которые выдал преподаватель
    'SECRET_KEY', --не забудьте поменять на настоящие, которые выдал преподаватель
    'Parquet'--тут указывает формат файла, в нашем случае это паркет, удобный и легковыесный формат хранения)  
select 
    1 as first, 2 as second, 3 as third 
from system.one
settings --здесь указываются дополнительные настройки при выполнении запроса 
s3_truncate_on_insert=1 --указываем перезапись файла, чтоб не получать ошибку о существующем файле, 
--будьте внимательны, чтоб случайно не перезаписать важные данные
;

--чтение файла происходит похожим образом
select * from s3( 
	'https://storage.yandexcloud.net/dad-ksu-datalab/DATA/test_file.parquet',
    'ACCESS_KEY',
    'SECRET_KEY',
    'Parquet')
;
--Clickhouse не всеглда может сам определить структуру файла, тогда необходимо будет указать ее вручную в параметре structure
select * from s3( 
	'https://storage.yandexcloud.net/dad-ksu-datalab/DATA/test_file.parquet',
    'ACCESS_KEY',
    'SECRET_KEY',
    'Parquet',
    structure='first UInt16, second UInt16, third UInt16')
;

--чтоб не светить чувствительные данные, можно использовать именованные коллекции
--запись
INSERT INTO FUNCTION s3(s3_dad_ksu_datalab, 
	filename='dad-ksu-datalab/DATA/test_file.parquet', --тогда требуется указать имя файла, начиная с бакета
    format='Parquet'
    )  
select 1 as first, 2 as second from system.one
settings 
s3_truncate_on_insert=1

--чтение
select * from s3(s3_dad_ksu_datalab, 
	filename='dad-ksu-datalab/DATA/test_file.parquet', --тогда требуется указать имя файла, начиная с бакета
    format='Parquet', --и формат файла
    structure='first UInt16, second UInt16' --возможно не потребуется, но лучше знать как это делается
    )  
```
---

### Весь код, описанный ниже будет работать только с Apache Airflow, доступ с любых других адресов в бакет запрещен. 

---

```python 

import boto3 #эта библиотека предназначена для работы с API S3
import urllib3
import datetime

urllib3.disable_warnings() # отключение предупреждений, чтоб не засоряли лог


endpoint_url = 'https://storage.yandexcloud.net' # здесь указываем эндпоинт ресурса, где расположено хранилище
access = os.getenv('ACCESS_KEY') # здесь указываем ACCESS_KEY, выданный вам преподавателем
secret = os.getenv('SECRET_KEY') # здесь указываем SECRET_KEY, выданный вам преподавателем
bucket = 'dad-ksu-datalab' # здесь указывается имя бакета, это так называемая ячейка, где хранятся наши данные 

session = boto3.session.Session() # создание сессии для доступа к хранилищу
s3 = session.client( #создание клиента для доступа к хранилищу, указываем адрес и данные авторизации
    service_name='s3',
    endpoint_url=endpoint_url,
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    verify=False
)

# ниже показано как получить список всех файлов в бакете
start_after = '' # в эту переменную будем записывать имя последнего полученного имени файла
obj_lst = [] # в этот список будм складывать имена всех файлов в нашем хранилище
while True:
    objs = s3.list_objects_v2(Bucket=bucket, StartAfter=start_after) # таким образом получаем список файлов с текущей страницы

    # проверяем последнюю полученную страницу на пустоту
    if objs['KeyCount'] > 0:
        start_after = objs['Contents'][-1]['Key']
    else:
        break # останавливаем цикл, если страница пустая

    obj_lst += [i['Key'] for i in objs['Contents']] # записываем имена в наш список-накопитель

print(obj_lst)
# список файлов будет выглядеть таким образом
#['DATA/client_segments.parquet', 'DATA/client_segments_1.parquet',]


# здесь будем проходить циклом по всем объектам чтоб вычитать их и записать, например, с новыми именами
for key in obj_lst:
    
    print(key, 'start', datetime.datetime.now())
    
    # забираем метаданные объекта
    get_object_response = s3.get_object(Bucket=bucket,Key=key) 
    
    # из метаданных забираем тело объекта и вычитываем его в переменную
    data = get_object_response['Body'].read()

    #Вариант 1. Открываем файл в бинарном виде и записываем в него полученные данные
    with open('buffer.parquet', 'wb') as file:
        file.write(data)

    # после записи используем метод для записи. 
    # в аргументах указываем какой файл берем, 
    # бакет, в который записываем, и имя файла, 
    # с которым он будет записан в хранилище
    s3.upload_file('buffer.parquet', bucket, f'{key}_new')

    # Вариант 2. Записываем данные в S3 напрямую из памяти. 
    # Это действие не требует лишней записи на диск, но имеет ограничение по памяти
    s3.put_object(Bucket=bucket, Key=f'{key}_new', Body=data)

    print(key, 'complete', datetime.datetime.now())


# после перезаписи файла мы можем удалить старые
for file in obj_lst:
    # вызываем метод, который удаляет файл
    res = s3.delete_object(Bucket=bucket_prod, Key=file)    
    # смотрим результат удаления файла 
    print(file, res['ResponseMetadata']['HTTPStatusCode'])

```

---

### Создание DAGа в Apache Airflow

```python

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
import datetime
import sys, os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))) #немного магии, добавляем путь, чтоб импортировать подзадачу из папки subtask_scripts
from subtask_scripts import subtask_from_folder #импортируем файл с функцией

default_args = {
    'owner': 'airflow', #владелец дага
    'depends_on_past': False, #зависимость от предыдущего
    'start_date': datetime.datetime(2020, 7, 1, 0, 0), #дата старта, раньше наступления этой даты даг не запустится
    'email': ['your_email@domen'], # имейл, на который будет отправлено уведомление
    'email_on_failure': False, #флаг отправлять ли сообщение при ошибке
    'email_on_retry': False, #флаг отправлять ли сообщение о перезапуске
    'retries': 0, #количество перезапусков в случае неудачи
    'retry_delay': datetime.timedelta(minutes=1), #сколько ждать после падения перед перезапуском
    'pool': 'default' #пул, в котором будет жить даг
}

# здесь описываем функцию, которую будем вызывать
# так делать плохо в файле, где описан даг, 
# функции, которые выполняют работу необходимо размещать в отдельных файлах 
# но для учебного примера не страшно
def test_python(arg='User'):
    print(f'SUCCESS {arg}!!!')


with DAG(
    dag_id="test_dag_3", #это уникальное имя дага, если оно совпадет с каким либо другим, то они будут перезаписывать друг друга
    default_args=default_args, #сюда передаем аргументы, которые описали выше, на самом деле их существует больше, чем описано, но этого достаточно
    schedule=None, #здесь указывается расписание, по которому следует запускать даг в cron формате, либо с использованием декораторов
    start_date=days_ago(0), #дата старта
    catchup=False, #этот параметр указывает стоит ли запускать даг за пропущенные даты
    tags=["test"], #здесь указываются теги, чтоб можно было с легкостью найти свой даг в веб интерфейсе
) as dag:


    task_1 = PythonOperator(#так как у нас функция написанная на питоне, то используем соответствующий оператор
        task_id='test_wo_arg',# уникальное, в рамках дага, наименовние задачи
        python_callable=test_python, #имя функции, которая будет исполняться оператором
        dag=dag #объект дага, к которому будет привязана задача
    )

    task_2 = PythonOperator(#так как у нас функция написанная на питоне, то используем соответствующий оператор
        task_id='test_with_arg',# уникальное, в рамках дага, наименовние задачи
        python_callable=test_python, #имя функции, которая будет исполняться оператором
        op_kwargs={'arg': 'Unknown'}, # таким образом можно передать именованные аргументы в функцию
        dag=dag #объект дага, к которому будет привязана задача
    )

        task_3 = PythonOperator(#так как у нас функция написанная на питоне, то используем соответствующий оператор
        task_id='test_from_subrtask',# уникальное, в рамках дага, наименовние задачи
        python_callable=subtask_from_folder.task_from_folder, #имя функции, которая будет исполняться оператором
        dag=dag #объект дага, к которому будет привязана задача
    )

    task_1 >> task_2 >> task_3 #таким образом мы выстраиваем последовательное выполнение задач

```