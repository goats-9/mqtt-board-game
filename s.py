import sys
import paho.mqtt.client as mqttClient

# Function to parse the received message
def parse_message(message):
    try:
        data = eval(message.decode("utf-8"))  # Convert bytes to dictionary
        return data
    except Exception as e:
        print("Error parsing message:", e)
        return None

# Function to check if two players are adjacent
def is_adjacent(player1, player2):
    return abs(player1['x'] - player2['x']) <= 1 and abs(player1['y'] - player2['y']) <= 1

# Function to check if a player is killed
def check_player_killed(player, other_players):
    for other_player_id, other_player in enumerate(other_players):
        if other_player and other_player['power'] == 1 and player['power'] == 0 and is_adjacent(player, other_player):
            return True, other_player_id
        elif player['power'] == 1 and other_player and other_player['power'] == 0 and is_adjacent(other_player, player):
            return True, other_player_id
        elif other_player and other_player['power'] == 1 and player['power'] == 1 and is_adjacent(player, other_player):
            return True, other_player_id
        elif other_player and other_player['power'] == 1 and player['power'] == 1 and is_adjacent(other_player, player):
            return True, other_player_id
    return False, None

def on_message(client, userdata, message):
    player_name = message.topic
    player_id = int(player_name.split("-")[-1])  # Extract player ID from topic
    data = parse_message(message.payload)
    
    if player_name.startswith("location/"):
        print("Received data for player {}:".format(player_id), data)
        
        if player_id < total_players:  # Collecting data for the first round of players
            all_players[player_id] = data
        else:  # After the first round, start checking for kills
            # Check if the player is killed
            killed, killed_player_id = check_player_killed(data, all_players)
            
            if killed:
                print("Player {} was killed by player {}.".format(killed_player_id, player_id))
                # Unsubscribe from the killed player's topic
                client.unsubscribe("location/player-{}".format(killed_player_id))

def subscribe_to_players(client, total_players):
    for i in range(1, total_players + 1):
        client.subscribe("location/player-{}".format(i))

# Initialize MQTT client
client_name = "sub"
broker_address = "localhost"  # Change this to your broker address
client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1, client_name)  # create new instance
client.on_message = on_message

# Connect to broker
client.connect(broker_address)
client.loop_start()

# Take the total number of players as argument
if len(sys.argv) != 2:
    print("Usage: python3 sub.py <total_players>")
    sys.exit(1)

total_players = int(sys.argv[1])

# List to store all players' data for the first round
all_players = [None] * total_players

# Subscribe to topics for all players
subscribe_to_players(client, total_players)

try:
    while True:
        pass
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
