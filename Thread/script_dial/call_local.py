import time
import requests


number_dst = str(1106)
# create channel did
url = 'https://ge.happydebt.kz:8089/ari/channels/create?endpoint=PJSIP%2F' + number_dst + '&app=incoming&formats=ulaw&api_key=root:3rptn30t'
header = {'content-type': 'application/json'}
data = requests.post(url, headers=header)
json_obj = data.json()
chn_did_dial = json_obj['id']
# print(json_obj)

id_bridge = str(745578936746486766854454467557384345)

r = requests.post(
    'https://ge.happydebt.kz:8089/ari/bridges?type=mixing&bridgeId=' + id_bridge + '&name=incoming&api_key=root:3rptn30t')
add_did_channel_in_bridge = requests.post(
    'https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '/addChannel?channel=' + chn_did_dial + '&api_key=root:3rptn30t')

url = 'https://ge.happydebt.kz:8089/ari/channels/externalMedia?app=incoming&external_host=192.168.127.58%3A7676&encapsulation=rtp&transport=udp&connection_type=client&format=ulaw&direction=both&data=vaga&api_key=root:3rptn30t'
# print(url)
header = {'content-type': 'application/json'}

media_send = requests.post(url, headers=header)
json_obj_media = media_send.json()
media_channel_id = json_obj_media['id']
print(media_channel_id)
print(json_obj_media)

add_media_bridge = requests.post(
    'https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '/addChannel?channel=' + media_channel_id + '&api_key=root:3rptn30t')
print("Dial did channel")
req_send_dial = requests.post(
    'https://ge.happydebt.kz:8089/ari/channels/' + chn_did_dial + '/dial?api_key=root:3rptn30t')
# print(req_send_dial.json())
# req_media_dial = requests.post(
#     'https://ge.happydebt.kz:8089/ari/channels/' + media_channel_id + '/dial?api_key=root:3rptn30t')
# kill channel
time.sleep(1)
r_kill_channel_media = requests.delete('https://ge.happydebt.kz:8089/ari/channels/' + str(media_channel_id) + '?api_key=root:3rptn30t')
r_kill_channel_did = requests.delete('https://ge.happydebt.kz:8089/ari/channels/' + str(chn_did_dial) + '?api_key=root:3rptn30t')
# delete bridges
r_kill_bridge = requests.delete('https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '?api_key=root:3rptn30t')
