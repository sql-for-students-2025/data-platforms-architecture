# Инструкция: продюсер и консьюмер на Python

## 1. Подготовка окружения

Установите библиотеку `pika` и `python-dotenv`:

```bash
pip install pika python-dotenv
```

Создайте файл `.env` в папке с проектом. В нём хранятся параметры подключения (их выдаёт преподаватель):

```
RABBITMQ_HOST=хост_rabbit_mq
RABBITMQ_PORT=5672
RABBITMQ_USER=ваш_логин
RABBITMQ_PASS=ваш_пароль
```

Важно: порт для Python-кода — **5672** (AMQP).

## 2. Общие принципы

- Producer (продюсер) — отправляет сообщения в RabbitMQ.
- Consumer (консьюмер) — читает сообщения из RabbitMQ.
- Сообщение публикуется не «в очередь», а в **exchange** (обменник). Exchange по правилам (bindings) раскладывает сообщение в очереди.
- Если использовать `exchange=''` (пустая строка), сообщение попадёт напрямую в очередь с именем, равным `routing_key`. Это самый простой вариант для начала.
- Имена очередей студентов должны начинаться с логина: `ivanov_ii_sch.my_queue`. Иначе RabbitMQ вернёт ошибку `ACCESS_REFUSED`.

## 3. Продюсер (отправка сообщений)

Файл `producer.py`:

```python
import json
import os

import pika
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

HOST = os.getenv("RABBITMQ_HOST")
PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
USER = os.getenv("RABBITMQ_USER")
PASS = os.getenv("RABBITMQ_PASS")

# Имя очереди. ОБЯЗАТЕЛЬНО начинается с вашего логина.
QUEUE = f"{USER}.my_queue"

# 1. Учётные данные и параметры подключения
credentials = pika.PlainCredentials(USER, PASS)
parameters = pika.ConnectionParameters(
    host=HOST,
    port=PORT,
    virtual_host="/",
    credentials=credentials,
    heartbeat=600,                  # keep-alive, чтобы соединение не рвалось
    blocked_connection_timeout=300,
)

# 2. Устанавливаем соединение и создаём канал
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# 3. Объявляем очередь.
#    durable=True — очередь переживёт перезапуск RabbitMQ.
#    Если очередь уже существует с другими аргументами — будет ошибка.
channel.queue_declare(queue=QUEUE, durable=True)

# 4. Формируем сообщение (словарь -> JSON-строка -> байты)
message = {
    "student": USER,
    "task": "lesson_8",
    "payload": "произвольные данные",
}
body = json.dumps(message, ensure_ascii=False).encode("utf-8")

# 5. Публикуем.
#    exchange='' — default exchange, routing_key = имя очереди.
#    delivery_mode=2 — сообщение persistent (переживёт перезапуск брокера).
channel.basic_publish(
    exchange="",
    routing_key=QUEUE,
    body=body,
    properties=pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2,
    ),
)

print(f"Отправлено в {QUEUE}: {message}")

# 6. Закрываем соединение
connection.close()
```

Запуск:

```bash
python producer.py
```

## 4. Консьюмер (чтение сообщений)

Файл `consumer.py`:

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

QUEUE = f"{USER}.my_queue"

credentials = pika.PlainCredentials(USER, PASS)
parameters = pika.ConnectionParameters(
    host=HOST,
    port=PORT,
    virtual_host="/",
    credentials=credentials,
    heartbeat=600,
    blocked_connection_timeout=300,
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Объявляем очередь. Если её ещё нет — создастся.
# Аргументы должны совпадать с теми, что использовал продюсер.
channel.queue_declare(queue=QUEUE, durable=True)

# Ограничиваем количество неподтверждённых сообщений на канале.
# RabbitMQ не выдаст консьюмеру больше одного сообщения за раз,
# пока предыдущее не подтверждено (basic_ack).
channel.basic_qos(prefetch_count=1)


def callback(ch, method, properties, body):
    """
    Вызывается на каждое полученное сообщение.
    ch — канал, method — метаданные доставки (в т.ч. delivery_tag),
    properties — свойства сообщения, body — тело (bytes).
    """
    try:
        message = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        message = {"_raw": body.decode("utf-8", errors="replace")}

    print(f"Получено: {message}")

    # Подтверждаем обработку. Без basic_ack сообщение останется
    # в состоянии unacked и при перезапуске будет доставлено снова.
    ch.basic_ack(delivery_tag=method.delivery_tag)

    # Альтернативы:
    # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    #   — вернуть сообщение в очередь (например, при временной ошибке)
    # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    #   — отбросить сообщение (или отправить в DLQ, если настроен)


# Подписываемся на очередь
channel.basic_consume(
    queue=QUEUE,
    on_message_callback=callback,
    auto_ack=False,   # ack делаем вручную в callback
)

print(f"Ожидание сообщений из {QUEUE}. Ctrl+C для выхода.")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
finally:
    connection.close()
```

Запуск:

```bash
python consumer.py
```

## 5. Чтение сообщений из очередей преподавателя

Созданы очереди `sales.queue`, `stock.queue`, `returns.queue`, `ecom.queue`, `loyalty.queue`, `supply.queue`, `movement.queue`, `store_eff.queue`, `delivery.queue`, `mobile.queue`. Студенту выдано право `read` на них.

Это значит:
- Читать (`basic_get`, `basic_consume`) — можно.
- Объявлять (`queue_declare`) с теми же аргументами — можно, но если аргументы не совпадут, будет ошибка. Проще не объявлять, а сразу читать.
- Публиковать в них — нельзя (`ACCESS_REFUSED`).
- Создавать очереди с такими именами — нельзя.

Пример консьюмера для чтения одной очереди преподавателя:

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

credentials = pika.PlainCredentials(USER, PASS)
parameters = pika.ConnectionParameters(
    host=HOST, port=PORT, virtual_host="/", credentials=credentials
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# prefetch_count=1 — не забирать больше одного сообщения за раз
channel.basic_qos(prefetch_count=1)


def callback(ch, method, properties, body):
    message = json.loads(body.decode("utf-8"))
    print(f"[sales] {message.get('event_id')} | {message.get('event_type')}")
    # Подтверждаем: сообщение удалится из очереди
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(
    queue=QUEUE,
    on_message_callback=callback,
    auto_ack=False,
)

print(f"Чтение из {QUEUE}. Ctrl+C для выхода.")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
finally:
    connection.close()
```

Важно: если несколько студентов одновременно читают `sales.queue`, RabbitMQ распределит сообщения между ними (round-robin). Каждый студент получит только часть сообщений.

## 6. Типичные ошибки и что они значат

- `AMQPConnectionError` — не удалось установить TCP-соединение. Проверьте `RABBITMQ_HOST`, порт 5672 и сетевой доступ (на учебном стенде часто нужен `kubectl port-forward` или доступ изнутри кластера).
- `ProbableAuthenticationError` / `ACCESS_REFUSED` при подключении — неверный логин/пароль или нет прав на vhost `/`.
- `ACCESS_REFUSED - queue_declare` — вы пытаетесь создать очередь, имя которой не начинается с вашего логина, либо пытаетесь объявить чужую очередь с другими аргументами.
- `PRECONDITION_FAILED` — очередь уже существует, но с другими аргументами (например, `durable` или `x-message-ttl` не совпадают).
- Сообщение «висит» в unacked — вы не вызвали `basic_ack` в callback, либо вызвали, но с ошибкой в коде до этого.