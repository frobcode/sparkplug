import amqp
import time

# need to wait for consumer to ready the server
time.sleep(15)

connection = amqp.Connection(
    'rabbitmq',
    userid='guest',
    password='guest',
    virtual_host='/'
)
connection.connect()  # validate properties
routing_key = 'events'
exchange = 'postoffice'
channel = connection.channel()

for i in range(64 * 1024, -1, -1):
    msg = amqp.Message(str(i))
    channel.basic_publish(msg, exchange=exchange, routing_key=routing_key)
    time.sleep(1.0 / 1024.0)

connection.close()
