# module server_thread_udp

# system
import socket
import time
import pika
from datetime import datetime
# from _thread import *

# audio
from pydub import AudioSegment
from pydub.playback import play as pydub_play

# autoresponder
from chat_assistent.autoresponder_detect.autoresponder_api import AutoResponderDetector, object_load
from chat_assistent.tools.audio_processing import audio_trim_silence


def publisher_rabbitmq(message: str):
    credentials = pika.PlainCredentials(username='admin', password='3rptn30t')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit', port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='test', durable=True, exclusive=False, auto_delete=False, arguments={})
    channel.basic_publish(exchange='assist', routing_key='test', body=message.encode())
    channel.close()
    connection.close()


if __name__ == '__main__':
    # load autodial detector
    detector = object_load('chat_assistent/autoresponder_detect/autoresponder_model.pkl')

    # audio settings
    sampling_rate = 8000
    seconds = 10 # read enough data for 1 second

    # socket init
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # создаем объект сокета сервера
    hostname = socket.gethostname()  # получаем имя хоста локальной машины
    port = 7676  # устанавливаем порт сервера
    server.bind(('', port))  # привязываем сокет сервера к хосту и порту

    # run server
    print(f"Server running {hostname}")
    while True:
        data = server.recvfrom(seconds*sampling_rate)
        if data:
            client_ip, client_port = data[1]
            publisher_rabbitmq(str({'id': client_port, 'status': 'Start'}))
            print(data[1])

            """
                save audio data
            """
            audio_data = data[0]
            filename = f"/audio/audio_{client_port}_{int(datetime.now().timestamp())}.ulaw"
            with open(filename, "ab") as file:
                file.write(audio_data)

            # pydub_play(filename)
            """
                autodial detect
            """
            # trim silence
            # ret, audio_data = audio_trim_silence(
            #    audio_data=audio_data,
            #    audio_fmt='wav',
            #    silence_thresh_db=20
            # )

            # check if audio_data is not silence
            status_msg = 'Stop'
            #if not (ret < 0):
                # detect
                # result_id = detector.predict_from_memory(audio_data)[0]

                # update status
                # status_msg = detector.classes_names[result_id]


            # time.sleep(1)
            publisher_rabbitmq(str({'id': client_port, 'status': status_msg}))
