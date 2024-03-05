import time
import requests
from pymongo import MongoClient, UpdateOne, UpdateMany, InsertOne, DeleteOne, ReplaceOne

# number_dst = str(77757757775)
number_dst = str(77077274012)


# number_dst = str(77012770034)
# number_dst = str(77472662816)

mng_host = 'deploy.happydebt.kz'
mng_port = '27017'
def __db_object():
    try:
        mng_url = 'mongodb://' + mng_host + ':' + mng_port + '/'
        print(mng_url)
        client = MongoClient(mng_url)
        mydb = client['gepard']
        return mydb
    except Exception as e:
        print(e)
        return False


def insert_db(json_data):
    try:
        dbconnect = __db_object()
        dbcollect = dbconnect['human_detect']
        dbcollect.insert_one(json_data)
        return True
    except Exception as e:
        print(e)
        return False

# numbers to call
wait_time = 30
numbers = [
    77077616580,
]
# number_dst = str(numbers[0])

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

url = 'https://ge.happydebt.kz:8089/ari/channels/externalMedia?app=incoming&external_host=192.168.127.58%3A7676&encapsulation=rtp&transport=udp&connection_type=client&format=alaw&direction=both&data=vaga&api_key=root:3rptn30t'
# print(url)
header = {'content-type': 'application/json'}
media_send = requests.post(url, headers=header)
json_obj_media = media_send.json()
media_channel_id = json_obj_media['id']
print(media_channel_id)
print(json_obj_media)

reslt = insert_db({
    "port": json_obj_media['channelvars']['UNICASTRTP_LOCAL_PORT'],
    "status": ""
})

add_media_bridge = requests.post(
    'https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '/addChannel?channel=' + media_channel_id + '&api_key=root:3rptn30t')
print("Dial did channel")
req_send_dial = requests.post(
    'https://ge.happydebt.kz:8089/ari/channels/' + chn_did_dial + '/dial?caller=77059244908&api_key=root:3rptn30t')
# print(req_send_dial.json())
# req_media_dial = requests.post(
#     'https://ge.happydebt.kz:8089/ari/channels/' + media_channel_id + '/dial?api_key=root:3rptn30t')
# kill channel
time.sleep(wait_time)
r_kill_channel_media = requests.delete(
    'https://ge.happydebt.kz:8089/ari/channels/' + str(media_channel_id) + '?api_key=root:3rptn30t')
r_kill_channel_did = requests.delete(
    'https://ge.happydebt.kz:8089/ari/channels/' + str(chn_did_dial) + '?api_key=root:3rptn30t')
# delete bridges
r_kill_bridge = requests.delete('https://ge.happydebt.kz:8089/ari/bridges/' + id_bridge + '?api_key=root:3rptn30t')
