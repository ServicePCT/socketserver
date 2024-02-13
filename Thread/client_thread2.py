import socket

client = socket.socket()  # создаем сокет клиента
hostname = socket.gethostname()  # получаем хост локальной машины
port = 789  # устанавливаем порт сервера
client.connect((hostname, port))  # подключаемся к серверу
# message = input("Input a text: ")  # вводим сообщение
client.send('{"client": 0001}'.encode())  # отправляем сообщение серверу
while True:
    data = client.recv(1024)  # получаем данные с сервера
    # print("Server sent: ", data.decode())
    if data.decode() == 5:
        break

client.close()
