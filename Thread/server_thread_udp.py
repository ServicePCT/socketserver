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
    audio_trim_silence_pydub,
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


def publisher_mongo(
    client: pymongo.MongoClient,
    port: int,
    status: int,
    status_str: str,
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
            {'status': f'{status}', 'status_str': status_str},
        )

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
    detector: AutoResponderDetector = object_load('./chat_assistent/autoresponder_detect/autoresponder_model.pkl')

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
    last_received_port = -1
    while True:
        # receive data
        status_code = STATUS_CODE_WAIT
        data = server.recvfrom(1024)

        # process data if received
        if data:
            """--------------------
                extract client info
            """
            client_ip, client_port = data[1]

            # check if we need to perform detection with client port (if no detection was run yet)
            doc = mongo_collection_find_one(mongo_client, dbname, colname, {'port':f'{client_port}', 'status':''})
            if not doc:
                if verbose and last_received_port != client_port: 
                    last_received_port = client_port
                    print(f'status is already filled, skip this port: {client_port}')
                continue
            
            # create update_doc query
            update_doc = {'time_last_update': datetime.now().isoformat(sep=' ', timespec='seconds')}
            if not 'time_first_received' in doc: update_doc['time_first_received'] = datetime.now().isoformat(sep=' ', timespec='seconds')
            
            # update last time received rtp
            mongo_collection_update_one(
                client=mongo_client, 
                dbname=dbname, 
                colname=colname,
                query={'port':f'{client_port}'},
                update_doc=update_doc,
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
                # trim silence and resample the audio
                ret, audio_file_bytes = audio_trim_silence_pydub(
                    audio=filename,
                    audio_fmt='wav',
                    silence_thresh_db=18,
                    resample_rate=detector.resample_rate,
                )

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
                        client=mongo_client,
                        port=client_port,
                        status=status_code,
                        status_str=detector.classes_names[status_code],
                        dbname=dbname,
                        colname=colname
                    )
        else:
            status_code = STATUS_CODE_CONN_LOST
            if verbose: print(f'STATUS CODE: {status_code} | NO_PACKET')


# end
