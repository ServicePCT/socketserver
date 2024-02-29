# module server_thread_udp

# system
import io
import os
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


def socket_send_packet(host, port, packet):
    # create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # connect to the client
    client_address = (host, port)
    client_socket.connect(client_address)

    status = True
    try:
        # send the message
        client_socket.sendall(packet)
    except:
        # failed to send message
        status = False

    # close the socket
    client_socket.close()
    return status


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
    READ_SIZE = 1024
    SAMPLE_RATE = 8000

    # socket init
    port = 7676
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    hostname = socket.gethostname()
    server.bind(('', port))

    if verbose:
        print(f"Server running {hostname}")

    # read and preprocess audio file
    filename = '/audio/ALBERT.wav'
    raw_alaw = audio_wav2alaw(filename)
    iobuf = io.BytesIO(raw_alaw)

    # run server
    seq = 0
    status_code = STATUS_CODE_WAIT
    while True:
        # receive data
        data = server.recvfrom(READ_SIZE)

        # process data if received
        if data:
            """--------------------
                extract client info and audio
            """
            client_ip, client_port = data[1]
            packet = rtp_packet_dpkt_decode(data[0])

            """--------------------
                try to send audio to client
            """
            # convert to bytes
            alaw_chunk = None if iobuf.tell() == len(iobuf.getbuffer()) else iobuf.read(READ_SIZE)
            if alaw_chunk:
                # create rtp packet
                rtp = rtp_packet_dpkt_encode(
                    payload=alaw_chunk,
                    payload_type=packet['payload_type'],
                    sequence_number=packet['sequence_number'],
                    timestamp=packet['timestamp'],
                    ssrc=packet['ssrc'],
                )

                # send packet
                if not server.sendto(rtp, data[1]):
                    print('! error sendto')
            else:
                time.sleep(3)
                iobuf.seek(0)

            time.sleep(0.12)
            '''
            # read audio
            filename = '/audio/ALBERT.wav'
            audio = AudioSegment.from_wav(filename)
            iobuf = io.BytesIO(audio.raw_data)

            # send audio to client
            print(f'{client_ip}::{client_port}')
            wav_data = iobuf.read(READ_SIZE)
            timestamp_counter = int(READ_SIZE * SAMPLE_RATE) #packet['timestamp']
            print(timestamp_counter)
            while wav_data:
                # convert to bytes
                alaw_data = audioop.lin2alaw(wav_data, audio.sample_width)

                # create rtp packet
                rtp_packet = rtp_packet_dpkt_encode(
                    payload=alaw_data,
                    payload_type=packet['payload_type'],
                    sequence_number=seq,
                    timestamp=timestamp_counter,
                    ssrc=packet['ssrc']+1,
                )

                # send
                #if socket_send_packet(client_ip, client_port, rtp_packet):
                if server.sendto(rtp_packet, data[1]):
                    wav_data = iobuf.read(READ_SIZE)
                    seq = (seq + 1) & 0xFFFF
                    timestamp_counter += len(alaw_data)
                else:
                    print('error send!')

                #time.sleep(0.020)
            print(f'packet(pt: {packet["payload_type"]}, sq: {seq}, ts: {timestamp_counter}, ssrc: {packet["ssrc"]+1})')
            print('next:')
            '''

            '''
            packet = rtp_packet_dpkt_decode(data[0])
            rtp = rtp_packet_dpkt_encode(
                payload=packet['payload'],
                payload_type=packet['payload_type'],
                sequence_number=packet['sequence_number'],
                timestamp=packet['timestamp'],
                ssrc=packet['ssrc'],
            )
            if not server.sendto(rtp, data[1]):
                print('! error sendto')
            '''
        else:
            status_code = STATUS_CODE_WAIT


# end
