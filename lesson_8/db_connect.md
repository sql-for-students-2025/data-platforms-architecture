# Инструкция: консьюмер на Python и работа с БД

## 1. Подготовка окружения

Установите библиотеку `psycopg2`, если на MacOS возникает ошибка при установке, то используйте установку библиотеки `psycopg2-binary`:

```bash
pip install psycopg2
```

Создайте файл `.env` в папке с проектом. В нём хранятся параметры подключения:

```
PG_HOST=хост_postgresql
PG_PORT=6432
PG_USER=ваш_логин
PG_PASSWORD=ваш_пароль
```

## 2. Создание подключения, курсора и выполнение запроса. 

```python
import psycopg2
from dotenv import load_dotenv
import os 
load_dotenv() #если файл .env лежит в той же папке, что и скрипт, то ничего указывать не нужно. 
#load_dotenv('path_to_env') #если файл .env лежит в другой папке, то необходимо указать полный путь до него. 
# Пример для UNIX-систем load_dotenv('/Users/user_name/my_scripts/pg_project/.env')
# Пример для Windows-систем load_dotenv(r'C:\Users\user_name\my_scripts\pg_project\.env')

#Получаем переменные из окружения. Заметьте, что при отсутствии соответствующей переменной в файле .env будет подставленно значение по умолнчанию, которое идет вторым в скобках
PG_HOST = os.getenv('PG_HOST', '')
PG_USER = os.getenv('PG_USER', '')
PG_PASSWORD = os.getenv('PG_PASSWORD', '')
PG_PORT = os.getenv('PG_PORT', 6432)
PG_DB_NAME = os.getenv('PG_DB_NAME', 'postgres')

#создаем объект подключения к БД
conn = psycopg2.connect(
    database=PG_DB_NAME, 
    user=PG_USER, 
    password=PG_PASSWORD, 
    port=PG_PORT, 
    host=PG_HOST
)

# Создаем курсор, именно он будет выполнять команты
cursor = conn.cursor()

# Пример отправки команды для выполнения в БД
cursor.execute('select 1;')

# метод cursor.fetchall() записывает в переменную result все полученные строки в виде списка [[line_1], [line_2], [line_3] ... [line_n]]. Повторные вызовы метода вернут пустоту. 
result = cursor.fetchall()

#метод cursor.fetchone() записывает в переменную result первую строку из полученных и смещает указатель на следующую, при этом строки из буфера cursor не удаляются. К ним можно вернуться. 
result = cursor.fetchone()

# Вывод результата в консоль
print(result)

# Чтоб не переполнять пул подключений необходимо закрывать курсор и подключение к БД, после окончания использования. 
cursor.close()
conn.close()
```

Есть более краткая запись через оператор контекста `with`:

```python

#создаем объект подключения к БД
with conn = psycopg2.connect(
    database=PG_DB_NAME, 
    user=PG_USER, 
    password=PG_PASSWORD, 
    port=PG_PORT, 
    host=PG_HOST
) as conn:

# Создаем курсор, именно он будет выполнять команты
    with conn.cursor() as cursor:

        # Пример отправки команды для выполнения в БД
        cursor.execute('select 1;')

        # метод cursor.fetchall() записывает в переменную result все полученные строки в виде списка [[line_1], [line_2], [line_3] ... [line_n]]. Повторные вызовы метода вернут пустоту. 
        result = cursor.fetchall()

        #метод cursor.fetchone() записывает в переменную result первую строку из полученных и смещает указатель на следующую, при этом строки из буфера cursor не удаляются. К ним можно вернуться. 
        result = cursor.fetchone()

        # Вывод результата в консоль
        print(result)

        # Заметьте, что нет вызова метода закрытия подключения, потому что оператор with сделает это самостоятельно
        # Такой способ работает немного медленнее, но делает код чище и нет необходимости следить за подключениями к БД
```


## 3. Библиотека json

Данная библиотека имеется в стандартном наборе python и не требует отдельной установки. 
Она позволяет работать с объектами типа json, которые возвращаются из сообщений RabbitMQ. 

Например у нас приходит сообщение:

```json
{
    'event_id': '2afbf7cf-6582-4424-848b-a4bb5fa85a4d',
    'event_type': 'receipt_line',
    'event_time': '2026-10-29T15:20:42.411246Z',
    'receipt_id': 'R-0879460',
    'receipt_status': 'CANCELLED',
    'store_id': 'ST-100',
    'store_name': 'Магазин ST-100',
    'store_city': 'Казань',
    'store_region': 'ПФО',
    'product_id': 'PRD-00862',
    'product_name': 'Товар PRD-00862',
    'product_category': 'Электроника',
    'product_brand': 'Brand-5',
    'customer_id': 'CUST-001349',
    'customer_segment': 'Новый',
    'quantity': 2,
    'gross_amount': 8505.73,
    'discount_amount': 1433.98,
    'net_amount': 7071.75,
    'cost_amount': 4243.05
 }
```

Так как оно приходит к нам в виде строки, то нам необходимо его превратить в словарь, для более удобного парсинга. 
Делается это с помощью метода `json.loads(message)`

```python
import json

#....где-то здесь код получения сообщений, его тут нет, чтоб не загромождать документ. 


message = json.loads(recieved_message)
# таким образом мы преобразовали строку в объект dict и можем легко обращаться к его ключам и работаь со значениями. 
# если вы попробуете обратиться к ключу `event_id` до преобразования сообщения, то получите ошибку. Можете легко это проверить написав recieved_message['event_id']
```

## 4. Получение и коллекционирование сообщений из очереди

Ниже код, который забирает сообщения и складывает их в список, который позже можно использовать для преобразования и записи в БД. 

```python
import json
import os

import pika
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("RABBITMQ_HOST")
PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
USER = os.getenv("RABBITMQ_USER")
PASS = os.getenv("RABBITMQ_PASS")

# Очередь преподавателя. НЕ объявляем её — только читаем.
QUEUE = "sales.queue"

# Сколько сообщений собрать, прежде чем остановиться.
# None означает "читать, пока не нажмут Ctrl+C".
MAX_MESSAGES = 100

credentials = pika.PlainCredentials(USER, PASS)
parameters = pika.ConnectionParameters(
    host=HOST, port=PORT, virtual_host="/", credentials=credentials
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# prefetch_count=1 — не забирать больше одного сообщения за раз
channel.basic_qos(prefetch_count=1)

# Список, куда складываются все полученные сообщения.
# После завершения чтения его можно использовать для анализа,
# сохранения в файл, передачи в другую функцию и т.д.
collected = []


def callback(ch, method, properties, body):
    try:
        message = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        # Если пришло не-JSON, сохраняем как есть, чтобы не потерять данные
        message = {"_raw": body.decode("utf-8", errors="replace")}

    collected.append(message)
    print(f"[sales] {message.get('event_id')} | {message.get('event_type')} "
          f"(собрано: {len(collected)})")

    # Возвращаем сообщение в очередь, чтоб другие могли его прочитать
    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    # Если достигли лимита — аккуратно останавливаем чтение
    if MAX_MESSAGES is not None and len(collected) >= MAX_MESSAGES:
        ch.stop_consuming()


channel.basic_consume(
    queue=QUEUE,
    on_message_callback=callback,
    auto_ack=False,
)

print(f"Чтение из {QUEUE}. Ctrl+C для выхода.")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\nПрервано пользователем.")
    channel.stop_consuming()
finally:
    connection.close()

# Здесь collected уже полностью заполнен и доступен для дальнейшего использования. Все события лежат в списке collected
print(f"\nВсего собрано сообщений: {len(collected)}")

# Пример дальнейшего использования: сохранить в JSON-файл
with open("sales_collected.json", "w", encoding="utf-8") as f:
    #с помощью `json.dump` можно записать json объект в файл
    json.dump(collected, f, ensure_ascii=False, indent=2)
```

## 5. Парсинг сообщений и заливка их в БД

```python

# где-то здесь импорты и чтение env файла, не будем повторяться

# создаем подключение 
conn = psycopg2.connect(
    database=PG_DB_NAME, 
    user=PG_USER, 
    password=PG_PASSWORD, 
    port=PG_PORT, 
    host=PG_HOST
)
cursor = conn.cursor()

# можно перебрать сообщения в цикле и разобрать их "по косточкам"
for message in collected:
    new_line = []
    # тут происходит парсинг каждого сообщения для каждой таблицы. Например можно собрать справочники, факты и тд
    sale_id = message['event_id']
    new_line.append(sale_id)
    
    sale_date = datetime.datetime.strptime(line['event_time'].split('T')[0], '%Y-%M-%d')
    new_line.append(sale_date)
    #и так далее...

    # либо можно распарсить сообщение и залить в стейдж таблицу (но ее надо заранее. создать с определенными полями и типами), 
    # а уже из нее собрать все остальные уже с помощью sql
    new_line = message.values()

    # и залить в нужную таблицу значение строки. %s повторяется только раз, сколько вставляется столбцов. 
    # можно заменить %s на динамическое определение количества плейсхолдеров, чтоб не подстраиваться под каждую таблицу
    # вместо (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) вставить {",".join(["%s"]*len(new_line))} - это выражение компилирует строку нужной длины
    cursor.execute(f'''
        insert into ИМЯ_ВАШЕЙ_СХЕМЫ.ИМЯ_ТАБЛИЦЫ (ТУТ МОЖНО УКАЗАТЬ КОНКРЕТНЫЕ СТОЛБЦЫ, ЕСЛИ ВСТАВКА ИДЕТ НЕ ВО ВСЕ СТОЛБЦЫ ТАБЛИЦЫ) 
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', 
        new_line
    )
        
# либо собрать Pandas DataFrame из списка collected, создать справочники из этого датафрейма и смапить полученные значения для таблицы фактов
df = pd.DataFrame(data=collected)

# не забываем закрыть курсор и соединение, если не используем оператор with
cursor.close()
conn.close()

```
