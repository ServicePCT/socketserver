# module server_thread_udp

# system
import os
import time
import pika
import json
import socket
from datetime import datetime

# audio
from pydub import AudioSegment

# autoresponder
from chat_assistent.autoresponder_detect.autoresponder_api import AutoResponderDetector, object_load
from chat_assistent.tools.audio_processing import (
    audio_trim_silence,
    audio_resample,
    audio_alaw2wav,
    audio_get_duration,
    audio_get_sampling_rate,
    audio_save,
)


def packet_strip_rtp_header(packet: bytes) -> bytes:
    """Strips off RTP header and returns data payload

    Args:
        packet (bytes): rtp packet

    Returns:
        bytes: data payload
    """
    RTP_HEADER_SIZE = 12
    return packet[RTP_HEADER_SIZE:]


def publisher_rabbitmq(message: str):
    credentials = pika.PlainCredentials(username='admin', password='3rptn30t')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit', port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='test', durable=True, exclusive=False, auto_delete=False, arguments={})
    channel.basic_publish(exchange='assist', routing_key='test', body=message.encode())
    channel.close()
    connection.close()


"""
    STATUS CODES:
    code >= 0    =>    detector autodial codes
    code <  0    =>    server codes
           -1    =>    wait
           -2    =>    error: no packet received (connection lost)

    NOTIFICATIONS:
    The server notifies upon detection only. Refer to timeout when to kill the
    process.
"""
STATUS_CODE_WAIT = -1
STATUS_CODE_CONN_LOST = -2
if __name__ == '__main__':
    # init
    cache = True
    verbose = True

    # load autodial detector
    detector = object_load('chat_assistent/autoresponder_detect/autoresponder_model.pkl')

    # socket init
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # создаем объект сокета сервера
    hostname = socket.gethostname()     # получаем имя хоста локальной машины
    port = 7676                         # устанавливаем порт сервера
    server.bind(('', port))             # привязываем сокет сервера к хосту и порту

    if verbose:
        print(f"Server running {hostname}")

    # run server
    status_code = STATUS_CODE_WAIT
    while True:
        # receive data
        data = server.recvfrom(1024)

        # process data if received
        if data:
            """--------------------
                extract client info
            """
            client_ip, client_port = data[1]
            #publisher_rabbitmq(str({'id': client_port, 'status': 'Start'}))

            """--------------------
                save audio data
            """
            audio_data = data[0]
            filename = f"/audio/audio_{client_port}.wav"

            # convert to ulaw to wav
            audio_alaw2wav(
                filename,
                packet_strip_rtp_header(audio_data),
                mode='a' if os.path.exists(filename) else 'w'
            )

            """--------------------
                autodial detect
            """
            if audio_get_duration(filename) > detector.duration:
                # trim silence and resample the audio
                ret, audio_file_bytes = audio_trim_silence(
                    audio=filename,
                    audio_fmt='wav',
                    silence_thresh_db=20,
                    resample_rate=detector.resample_rate,
                )

                # ensure we have the required duration for recognition
                if audio_get_duration(audio_file_bytes) < detector.duration:
                    with open(filename, 'wb') as f: f.write(audio_file_bytes)
                    continue

                # ensure audio is not silence
                if not (ret < 0):
                    status_code = detector.predict_from_memory(audio_file_bytes)[0]

                    # cache file for further training
                    if cache:
                        with open(filename[:-4] + f'_{detector.classes_names[status_code]}_{datetime.now()}.wav', 'wb') as f:
                            f.write(audio_file_bytes)

                # remove the old file audio snippet
                os.remove(filename) if os.path.exists(filename) else None

                if verbose:
                    print(f'STATUS CODE: {client_port}:{status_code} |', 'NO PACKET' if status_code < 0 else detector.classes_names[status_code])

                # if recognized notify and exit
                if status_code >= 0:
                    msg = json.dumps({'id': f'{client_port}', 'status': f'{status_code}'})
                    publisher_rabbitmq(msg)
        else:
            status_code = STATUS_CODE_WAIT


# end
