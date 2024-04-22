import paho.mqtt.client as mqttClient
import time
import sys

# Function to read coordinates from the text file
def read_coordinates(filename):
    coordinates = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:  # Skip the first line
            parts = line.strip().split()
            x = int(parts[0])
            y = int(parts[1])
            power = int(parts[2])
            coordinates.append({"x": x, "y": y, "power": power})
    return coordinates

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected  # Use global variable
        Connected = True  # Signal connection
    else:
        print("Connection failed Return Code : ", rc)

def on_message(client, userdata, message):
    print("Player", message.payload,"was killed.")
    print("")

Connected = False  # Global variable for the state of the connection

# Check if the correct number of arguments is provided
if len(sys.argv) != 3:
    print("Usage: python3 script.py <player_id> <filename>")
    sys.exit(1)

client_name = "player-" + sys.argv[1]  # Add player_id to the client name
filename = sys.argv[2]  # Get filename from command-line arguments
broker_address = "127.0.0.1"  # Broker address
port = 1883  # Broker port default for MQTT

# Read coordinates from the text file
coordinates = read_coordinates(filename)

client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1, client_name)  # create new instance
client.on_connect = on_connect  # attach function to callback
client.on_message = on_message  # attach function to callback
client.connect(broker_address, port=port)  # connect to broker (login credentials)
client.loop_start()  # start the loop


while Connected != True:  # Wait for connection
    time.sleep(0.1)

# Subscribe to location/life topic
try:
    for coord in coordinates:
        client.publish("location/"+client_name, str(coord))
        client.subscribe("location/life")
        time.sleep(15)

except KeyboardInterrupt:
    print("exiting")
    client.disconnect()
    client.loop_stop()
    
