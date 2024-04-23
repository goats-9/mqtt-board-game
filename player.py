#!/usr/bin/env python3

"""
File        : player.py
Authors     : Debika Samanta and Gautam Singh
Purpose     : Client script to connect to board game server and handle gameplay.
"""
#########
# Imports
#########
import paho.mqtt.client as mqttClient
import time
import ast
import argparse
from collections import deque

#################
# Game state info
#################

players = {}        # Dictionary of queues of player states after each move indexed by player number
num = 0             # Player number assigned
server_addr = ''    # IP address of server to connect to
server_port = 0     # Port number of server to connect to
N = 0               # Total number of players
moves = []          # List of moves made by the player
killed = False      # Flag to determine whether the player has been killed

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
    """ Callback to update game state. """
    global players,  num
    recv_msg = ast.literal_eval(message.payload.decode('utf-8'))
    player_num = int(message.topic.split('/')[-1])
    # print("recv", player_num, recv_msg)
    # Ignore message if player is killed (deleted from game state)
    if player_num not in players.keys():
        return
    # Push message to queue if id is larger
    if not players[player_num]:
        players[player_num].append(recv_msg)
    elif recv_msg['id'] > players[player_num][-1]['id']:
        players[player_num].append(recv_msg)

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
# Dummy move at the end to determine winner
moves.append([0, 0, 0])

# Set up players' state
for i in range(1,N+1):
    player_name = f'player-{i}'
    players[i] = deque()

players[num].append({
    'id': -1,
    'loc': {
        'x': 0,
        'y': 0,      
    },
    'power': 0,
    'status': 1,
})

# Player flow

# Setup player and connect to MQTT broker
client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1, client_name)
client.on_connect = on_connect
client.on_message = on_message

client.connect(server_addr, server_port)

# Start player loop
client.loop_start()

# Subscribe to player topics
for i in range(1,N+1):
    if i != num:
        client.subscribe(f'players/{i}', qos=2)

try:
    # Wait for players to be online
    while True:
        # Publish health/connection status
        client.publish(f'players/{num}', str(players[num][-1]), qos=2)
        player_cnt = 0
        for idx, player in players.items():
            # Check player status at front of the queue
            if not player:
                continue
            while player and player[0]['id'] != -1:
                player.popleft()
            player_cnt += player[0]['status']
        if player_cnt >= N:
            break
        # Wait to receive opponents connection status
        time.sleep(1)
    # Players keep playing until they are killed
    while len(players.keys()) > 1:
        # Play next move
        j = players[num][-1]['id'] + 1
        move = moves[j]
        # Create new status
        player_stat = {
            'id': j,
            'loc': {
                'x': move[0],
                'y': move[1],
            },
            'status': int(not killed),
            'power': move[2]
        }
        # Update own game state
        players[num].append(player_stat)
        # Publish to other players
        client.publish(f'players/{num}', str(player_stat), qos=2)
        # If player is dead, disconnect
        if killed:
            break
        # Collect updated info
        while True:
            # Count of players whose info for current move is available
            cnt = 0
            for _, move_queue in players.items():
                while move_queue and move_queue[0]['id'] < j:
                    move_queue.popleft()
                if move_queue and move_queue[0]['id'] == j:
                    cnt += 1
            # All players alive must have up-to-date status
            if cnt == len(players.keys()):
                break
        # Find dead players and delete them
        del_list = []
        for idx, move_queue in players.items():
            if move_queue[0]['status'] == 0:
                del_list.append(idx)
        for val in del_list:
            del players[val]
        # Check if we are dead
        if players[num][0]['power'] == 1:
            continue
        for idx, move_queue in players.items():
            if idx == num or move_queue[0]['power'] == 0 or not is_adjacent(players[num][0]['loc'], move_queue[0]['loc']):
                continue
            # Print kill status
            print(f'Player {idx} kills player {num} at turn {j}.')
            # Update health status for next message
            killed = True
    if not killed:
        print(f'Winner: player {num}!')
except KeyboardInterrupt:
    print("exiting")

players[num][-1]['status'] = 0
client.publish(f'players/{num}', str(players[num][-1]), qos=2)
client.disconnect()
client.loop_stop() 