import socket

# client = socket.socket()  # создаем сокет клиента
# hostname = socket.gethostname()  # получаем хост локальной машины
# port = 789  # устанавливаем порт сервера
# client.connect((hostname, port))  # подключаемся к серверу
# message = input("Input a text: ")  # вводим сообщение
# client.send(message.encode())  # отправляем сообщение серверу
# data = client.recv(1024)  # получаем данные с сервера
# print("Server sent: ", data.decode())
# # client.close()
import pika

queue_from = 'test'
pm = 'param_conn'
# можно хранить аутетификацию таким образом.
# довольно удобно для большого количества серверов с разными паролями хостами
pm_dict = {'param_conn': {
    'host': 'deploy.happydebt.kz',
    'port': 5672,
    'auth': {'username': 'admin', 'password': '3rptn30t'}
}
}

credentials = pika.PlainCredentials(**pm_dict[pm]['auth'])
parameters = pika.ConnectionParameters(host=pm_dict[pm]['host'], port=pm_dict[pm]['port'], credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
# тут получаем количество сообщений в нашей очереди
cnt = channel.queue_declare(queue='test', durable=True, exclusive=False, auto_delete=False,
                            arguments={})  # .method.message_count

print("Start RabbitMQ client")


def callback(ch, method, properties, body, messages=''):
    print(body)
    # channel.close()
    # connection.close()


channel.basic_consume(queue='test', on_message_callback=callback, auto_ack=True)
channel.start_consuming()
