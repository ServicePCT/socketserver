# import socket
# import pika
# from _thread import *
#
#
# def publisher_rabbitmq(message: str):
#     credentials = pika.PlainCredentials(username='admin', password='3rptn30t')
#     connection = pika.BlockingConnection(
#         pika.ConnectionParameters(host='deploy.happydebt.kz', port=5672, credentials=credentials))
#     channel = connection.channel()
#     channel.queue_declare(queue='test', durable=True, exclusive=False, auto_delete=False, arguments={})
#     channel.basic_publish(exchange='assist', routing_key='test', body=message.encode())
#     channel.close()
#     connection.close()
#
#
# # функция для обработки каждого клиента
# def client_thread(conn, conn_addr: tuple):
#     conn_ip, conn_port = conn_addr
#     message = {'id': conn_port, 'status': 'Start'}
#     publisher_rabbitmq(str(message))
#     data = conn.recv(1024)  # получаем данные от клиента
#     message = data.decode()  # преобразуем байты в строку
#     print(f"Client sent: {message}")
#     message = message[::-1]  # инвертируем строку
#     conn.send(message.encode())  # отправляем сообщение клиенту
#     conn.close()  # закрываем подключение
#
#
# #
# #
# server = socket.socket()  # создаем объект сокета сервера
# hostname = socket.gethostname()  # получаем имя хоста локальной машины
# port = 789  # устанавливаем порт сервера
# server.bind((hostname, port))  # привязываем сокет сервера к хосту и порту
# server.listen(5)  # начинаем прослушиваение входящих подключений
# #
# print(f"Server running {hostname}")
# while True:
#     client, addr = server.accept()  # принимаем клиента
#     # start_new_thread(client_thread, (client, addr,))  # запускаем поток клиента
