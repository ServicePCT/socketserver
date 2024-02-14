import socket
import time
import pika
# from _thread import *

def publisher_rabbitmq(message: str):
    credentials = pika.PlainCredentials(username='admin', password='3rptn30t')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit', port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='test', durable=True, exclusive=False, auto_delete=False, arguments={})
    channel.basic_publish(exchange='assist', routing_key='test', body=message.encode())
    channel.close()
    connection.close()


server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # создаем объект сокета сервера
hostname = socket.gethostname()  # получаем имя хоста локальной машины
port = 7676  # устанавливаем порт сервера
server.bind(('', port))  # привязываем сокет сервера к хосту и порту
print(f"Server running {hostname}")
while True:
    data = server.recvfrom(1024)
    if data:
        client_ip, client_port = data[1]
        publisher_rabbitmq(str({'id': client_port, 'status': 'Start'}))
        print(data[1])
        # print(data[0])
        file = open("/audio/audio_" + str(client_port) + ".ulaw", "ab")
        file.write(data[0])
        file.close()
        # time.sleep(1)
        publisher_rabbitmq(str({'id': client_port, 'status': 'Stop'}))
