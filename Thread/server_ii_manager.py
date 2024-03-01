# module server_thread_udp

# system
import io
import os
import sys
import time
import pika
import json
from datetime import datetime

# socket
import ssl
import socket

# audio
import audioop
import librosa
from pydub import AudioSegment

# autodial
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from chat_assistent.tools.audio_processing import (
    audio_trim_silence,
    audio_resample,
    audio_alaw2wav,
    audio_wav2alaw,
    audio_get_duration,
    audio_get_sampling_rate,
    audio_save,
)
from chat_assistent.tools.rtp import (
    rtp_packet_dpkt_encode,
    rtp_packet_dpkt_decode,
)
from chat_assistent.tools.logging import log_print


def rabbitmq_publish(message: str, queue: str = 'test'):
    credentials = pika.PlainCredentials(username='admin', password='3rptn30t')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='rabbit',
            port=5672,
            credentials=credentials
    ))
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True, exclusive=False, auto_delete=False, arguments={})
    channel.basic_publish(exchange='assist', routing_key='test', body=message.encode())
    channel.close()
    connection.close()


def rabbitmq_receive(message: str):
    pass


if __name__ == '__main__':
    # init
    name = '[ ii_manager ]'
    verbose = True

    if verbose:
        log_print('Server running', start=name)

    # run server
    while True:
        # scan rabbit for port request
        # ...

        # post available port to rabbit
        # ...

        # start up ii_bot with port
        # ...
        pass



# end
