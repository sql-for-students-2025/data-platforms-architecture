import pika
from dotenv import load_dotenv
import os

load_dotenv()

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', '')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', '')

def callback(ch, method, properties, body):
    print(f" [x] Получено: {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)  # подтверждаем обработку
    # ch.basic_nack(requeue=True) # возвращаем в очередь

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
parameters = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=5672,                         
    virtual_host='/',
    credentials=credentials
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.basic_consume(
    queue='sales.queue',
    on_message_callback=callback
)

print('Ожидание сообщений. Ctrl+C для выхода')
channel.start_consuming()