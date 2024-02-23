# module server_thread_udp

# system
import io
import os
import time
import pika
import json
import socket
from datetime import datetime

# audio
import audioop
import librosa
from pydub import AudioSegment
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

    # socket init
    port = 7676
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    hostname = socket.gethostname()
    server.bind(('', port))

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
                extract client info and audio
            """
            client_ip, client_port = data[1]
            in_audio_data = data[0]

            """--------------------
                try to send audio to client
            """
            # read audio
            filename = '/audio/albert_11labs.wav'
            #out_audio_data = AudioSegment.from_wav(filename).set_frame_rate(8000)
            out_audio_data, _ = librosa.load(filename, sr=8000)

            # convert to bytes
            alaw_data = audioop.lin2alaw(out_audio_data.tobytes(), 1)
            out_audio_file = io.BytesIO(alaw_data)
            #out_audio_file = io.BytesIO()
            #audio_save(out_audio_file, out_audio_data, audio_format='wav', sample_rate=8000)

            # send audio to client
            print(f'{client_ip}::{client_port}')
            READ_SIZE = 1024
            s_data = out_audio_file.read(READ_SIZE)
            while s_data:
                if server.sendto(s_data, data[1]):
                    s_data = out_audio_file.read(READ_SIZE)

            # publisher_rabbitmq(msg)
        else:
            status_code = STATUS_CODE_WAIT


# end
