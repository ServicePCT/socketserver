# module server_thread_udp

# system
import io
import os
import sys
import time
import pika
import json
import pymongo
import socket
from datetime import datetime

# audio
from pydub import AudioSegment

# autoresponder
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from chat_assistent.autoresponder_detect.autoresponder_api import AutoResponderDetector, object_load
from chat_assistent.tools.audio_processing import (
    audio_trim_silence,
    audio_remove_silence,
    audio_resample,
    audio_alaw2wav,
    audio_get_duration,
    audio_get_sampling_rate,
    audio_save,
)
from chat_assistent.tools.rtp import (
    rtp_packet_encode,
    rtp_packet_dpkt_encode,
    rtp_packet_dpkt_decode,
    rtp_packet_decode,
)
from chat_assistent.tools.auxiliary import (
    aux_timestamp2str,
)
from chat_assistent.tools.mongo import (
    mongo_collection_update_one,
    mongo_collection_find_one,
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


def publisher_mongo(
    client: pymongo.MongoClient,
    port: int,
    status: int,
    dbname: str = 'gepard',
    colname: str = 'human_detect'
):
    # check if document with `port` has emtpy `status` and update with new value
    if mongo_collection_find_one(client, dbname, colname, {'port': f'{port}'}):
        mongo_collection_update_one(
            client,
            dbname,
            colname,
            {'port': f'{port}'},
            {'status': f'{status}'},
        )


def publisher_rabbitmq(message: str):
    # """ ----- OLD -----
    credentials = pika.PlainCredentials(username='admin', password='3rptn30t')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit', port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='test', durable=True, exclusive=False, auto_delete=False, arguments={})
    channel.basic_publish(exchange='assist', routing_key='test', body=message.encode())
    channel.close()
    connection.close()
    """

    # init rabbit credentials
    credentials = RabbitCredentials(
        host='rabbit',
        port=5672,
        username='admin',
        passwd='3rptn30t',
    )

    # publish
    with RabbitSession(credentials) as rs:
        rs.publish(
            message=message,
            queue='test',
            exchange='assist',
            routing_key='test',
        )
    """


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
    detector = object_load('../chat_assistent/autoresponder_detect/autoresponder_model.pkl')

    # init mongo session
    dbname = 'gepard'
    colname = 'human_detect'
    mongo_client = pymongo.MongoClient('mongodb://mongodb:27017/')

    # socket init
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)  # создаем объект сокета сервера
    hostname = socket.gethostname()     # получаем имя хоста локальной машины
    port = 7676                         # устанавливаем порт сервера
    server.bind(('', port))             # привязываем сокет сервера к хосту и порту

    if verbose:
        print(f"Server running {hostname}")

    # run server
    while True:
        # receive data
        status_code = STATUS_CODE_WAIT
        data = server.recvfrom(1024)

        # process data if received
        if data:
            """--------------------
                extract client info
            """
            # check if we need to perform detection with port
            client_ip, client_port = data[1]
            #if not mongo_collection_find_one(
            #    mongo_client, dbname, colname,
            #    {'port':f'{client_port}', 'status':''},
            #): continue

            # update last time received rtp
            mongo_collection_update_one(
                    mongo_client, dbname, colname,
                    {'port':f'{client_port}'},
                    {'time_last_update': datetime.now().isoformat(sep=" ", timespec="seconds")}
                )


            """--------------------
                decode RTP packet
            """
            packet = rtp_packet_dpkt_decode(data[0])

            """--------------------
                save audio data
            """
            audio_data = packet['payload']
            filename = f"/audio/audio_{client_port}.wav"

            # convert to ulaw to wav
            audio_alaw2wav(
                filename,
                audio_data,
                mode='a' if os.path.exists(filename) else 'w'
            )

            """--------------------
                autodial detect
            """
            if audio_get_duration(filename) > detector.duration*1.5:
                """----------- OPTION 1 ----------------"""
                # trim silence and resample the audio
                ret, audio_file_bytes = audio_trim_silence(
                    audio=filename,
                    audio_fmt='wav',
                    silence_thresh_db=20,
                    resample_rate=detector.resample_rate,
                )
                """----------- OPTION 2 ----------------"""
                # remove silence
                #audio_rsb = audio_remove_silence(
                #    audio=filename,
                #    audio_fmt='wav',
                #    silence_thresh_db=18,
                #    combined=True,
                #)[0]

                # save audio_file_bytes
                #audio_file_bytes = io.BytesIO()
                #audio_save(audio_file_bytes, audio_data=audio_rsb, audio_format='wav', sample_rate=8000)
                #audio_file_bytes = audio_file_bytes.read()
                #ret = -1 if audio_get_duration(filename) == audio_get_duration(audio_file_bytes) else 0
                """--------------------------------"""

                # ensure we have the required duration for recognition
                if audio_get_duration(audio_file_bytes) < detector.duration*0.8:
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
                    print(f'STATUS CODE: {client_port}:{status_code} |', 'WAIT' if status_code < 0 else detector.classes_names[status_code])

                # if recognized notify and exit
                if status_code >= 0:
                    publisher_mongo(
                        mongo_client,
                        client_port,
                        status_code,
                        dbname=dbname,
                        colname=colname
                    )
        else:
            status_code = STATUS_CODE_CONN_LOST
            if verbose: print(f'STATUS CODE: {status_code} | NO_PACKET')


# end
