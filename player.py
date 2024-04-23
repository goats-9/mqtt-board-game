#!/usr/bin/env python3

"""
File        : player.py
Authors     : Debika Samanta and Gautam Singh
Purpose     : Client script to connect to board game server and handle gameplay.
"""
#########
# Imports
#########
from paho.mqtt.reasoncodes import ReasonCode
import paho.mqtt.client as mqttClient
import time
import ast
import argparse

#################
# Game state info
#################

players = {}        # Dictionary of player states indexed by player name
num = 0             # Player number assigned
server_addr = ''    # IP address of server to connect to
server_port = 0     # Port number of server to connect to
N = 0               # Number of players alive
moves = []          # List of moves made by the player

def is_adjacent(p1: dict, p2: dict):
    """ Function to check whether locations `p1` and `p2` are adjacent to each other. """
    return abs(p1['x'] - p2['x']) + abs(p1['y'] - p2['y']) == 1

######################
# Callbacks for client
######################

def on_connect(client: mqttClient.Client, userdata, flags, rc):
    """ Callback to set connection status of client. """
    if rc == 0:
        global num
        print(f"Connected to broker as player-{num}")
    else:
        print("Connection failed, return code", rc)

def on_message(client: mqttClient.Client, userdata, message: mqttClient.MQTTMessage):
    """ Callback to update opponent player status. """
    global players, num
    recv_msg = ast.literal_eval(message.payload.decode('utf-8'))
    player_num = int(message.topic.split('/')[-1])
    print("recv", player_num, recv_msg)
    players[player_num] = recv_msg

# Initialization

# Argument parsing
parser = argparse.ArgumentParser(description='Script to connect to an MQTT server to play a board game.')
parser.add_argument('--server_addr', dest='server_addr', default='127.0.0.1', help='IP address of the MQTT broker to connect to (default: 127.0.0.1)')
parser.add_argument('--server_port', dest='server_port', default=1883, help='Port number on which the MQTT broker is running (default: 1833)', type=int)
parser.add_argument('-n', '--num', dest='num', help='Player number to be assigned', required=True, type=int)
args = parser.parse_args()

num = args.num
server_addr = args.server_addr
server_port = args.server_port

# Set up some variables
client_name = f'player-{num}'

# Read move file
with open(f'{client_name}.txt') as fh:
    L = fh.readlines()
    # Number of players
    N = int(L[0])
    # Moves
    L = L[1:]
    moves = [[int(x) for x in l.split()] for l in L]

# Set up players' state
for i in range(1,N+1):
    player_name = f'player-{i}'
    players[i] = {
        'loc': {
            'x': 0,
            'y': 0,
            'i': -1,
        },
        'power': 0,
        'status': 0,
    }

# Player flow

# Setup player and connect to MQTT broker
client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1, client_name, clean_session=True)
client.on_connect = on_connect
client.on_message = on_message

client.connect(server_addr, server_port)
# Publish health/connection status
players[num]['status'] = 1
client.publish(f'players/{num}', str(players[num]))

# Start player loop
client.loop_start()

# Subscribe to player topics
for i in range(1,N+1):
    if i != num:
        client.subscribe(f'players/{i}')

try:
    # Wait for players to be online
    while True:
        player_cnt = 0
        for player in players.values():
            player_cnt += player['status']
        print(player_cnt)
        if player_cnt >= N:
            break
        time.sleep(1)
    j = 0
    # Players keep playing until they are the only ones left on the server
    while True:
        # Find number of players on server
        player_cnt = 0
        for player in players.values():
            player_cnt += player['status']
        if player_cnt <= 1:
            break
        move = moves[j]
        # Publish updated status info
        players[num]['loc'] = {
            'x': move[0],
            'y': move[1],
            'i': j,
        }
        players[num]['power'] = move[2]
        client.publish(f'players/{num}', str(players[num]), retain=True, qos=2)
        # If player is dead, disconnect
        if players[num]['status'] == 0:
            break
        # Listen to other alive players' updated info
        # cnt maintains the number of players whose info is updated.
        while True:
            cnt = 0
            for player in players.values():
                if players[num]['loc']['i'] == player['loc']['i']:
                    cnt += 1
            if cnt >= player_cnt:
                break
        print(cnt, player_cnt)
        # Check if we are dead
        if players[num]['power'] == 1:
            continue
        for i in range(1,N+1):
            if i == num or players[i]['power'] == 0 or not is_adjacent(players[num]['loc'], players[i]['loc']):
                continue
            # Print kill status
            print(f'Player {i} kills player {num}.')
            # Update health status for next message
            players[num]['status'] = 0
        j = (j + 1)%len(moves)
    if players[num]['status'] == 1:
        print(f'Winner: player {num}!')
except KeyboardInterrupt:
    print("exiting")

players[num]['status'] = 0
client.publish(f'players/{num}', str(players[num]), retain=True)
client.disconnect()
client.loop_stop() 