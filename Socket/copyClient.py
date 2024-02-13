import socket


class ClientSocket:
    def __init__(self, host, port):
        self.socket = None
        self.host = host
        self.port = port

    def socket_create(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.host, self.port))
        while True:
            data = "Start"
            data_bytes = data.encode()
            self.socket.sendall(data_bytes)
            data_bytes = self.socket.recv(1024)
            data = data_bytes.decode("utf-8")
            print(data)
            if data == 'Human':
                print('Break')
                break


objSocket = ClientSocket("127.0.0.1", 4567)
objSocket.socket_create()
objSocket.connect()