# module call_ext_args

# system
import os
import time
import requests
import argparse
import subprocess


if __name__ == '__main__':
    # setup
    parser = argparse.ArgumentParser()
    parser.add_argument('--nums', required=True, help='phone numbers split by a comma ","')
    parser.add_argument('--autodial_server', required=True, help='autodial server')
    parser.add_argument('--wait', help='wait time in seconds before killing the call', type=float, default=1)
    parser.add_argument('--verbose', help='verbose output', action='store_true')

    # parse args
    args = parser.parse_args()

    # assert exists
    assert os.path.exists(args.autodial_server), f'autodial_server does not exist: <{args.autodial_server}>!'

    # get numbers
    numbers = args.nums.split(',')
    for i, number_dst in enumerate(numbers):
        # change 8 to 7
        number_dst = '7' + number_dst[1:]

        # verbose
        if args.verbose:
            print(f'-----------------------')
            print(f'({i}) CALLING: {number_dst}')

        # validate number
        if len(number_dst) != 11:
            if args.verbose: print(f'    INVALID: {number_dst}')
            continue
        
        """------------
            START
        """

        # start autodial server
        pid_autodial = subprocess.Popen(['python', args.autodial_server])
        
        # wait till the server starts up
        time.sleep(0.5)

        # create channel did
        url = 'https://ge.happydebt.kz:8089/ari/channels/create?endpoint=PJSIP%2F77059244900%2Fsip%3A' + number_dst + '%4046.227.186.229%3A5060&app=incoming&api_key=root:3rptn30t'
        header = {'content-type': 'application/json'}
        json_data_inc = {"variables": {
            "CALLERID(name)": "77059244908",
            "CALLERID(num)": "77059244908",
        }}
        data = requests.post(url, headers=header)
        json_obj = data.json()
        chn_did_dial = json_obj['id']
        # print(json_obj)

        id_bridge = str(7455755589367464)

        r = requests.post(
            'https://ge.happydebt.kz:8089/ari/bridges?type=mixing&bridgeId=' + id_bridge + '&name=incoming&api_key=root:3rptn30t')
        add_did_channel_in_bridge = requests.post(
            'https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '/addChannel?channel=' + chn_did_dial + '&api_key=root:3rptn30t')

        url='https://ge.happydebt.kz:8089/ari/channels/externalMedia?app=incoming&external_host=192.168.127.58%3A7676&encapsulation=rtp&transport=udp&connection_type=client&format=alaw&direction=both&data=vaga&api_key=root:3rptn30t'
        # print(url)
        header = {'content-type': 'application/json'}

        media_send = requests.post(url, headers=header)
        json_obj_media = media_send.json()
        media_channel_id = json_obj_media['id']
        # print(media_channel_id)
        # print(json_obj_media)

        add_media_bridge = requests.post(
            'https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '/addChannel?channel=' + media_channel_id + '&api_key=root:3rptn30t')
        print("Dial did channel")
        req_send_dial = requests.post(
            'https://ge.happydebt.kz:8089/ari/channels/' + chn_did_dial + '/dial?caller=77059244908&api_key=root:3rptn30t')
        # print(req_send_dial.json())
        # req_media_dial = requests.post(
        #     'https://ge.happydebt.kz:8089/ari/channels/' + media_channel_id + '/dial?api_key=root:3rptn30t')

        """------------
            SHUTDOWN
        """

        # wait for autodial server to shutdown
        pid_autodial.wait()

        # kill channel
        time.sleep(float(args.wait))
        r_kill_channel_media = requests.delete('https://ge.happydebt.kz:8089/ari/channels/' + str(media_channel_id) + '?api_key=root:3rptn30t')
        r_kill_channel_did = requests.delete('https://ge.happydebt.kz:8089/ari/channels/' + str(chn_did_dial) + '?api_key=root:3rptn30t')
        # delete bridges
        r_kill_bridge = requests.delete('https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '?api_key=root:3rptn30t')
        
        




