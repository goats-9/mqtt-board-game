#!/bin/bash

# Constant filename for player 1
filename="player-1.txt"

# Read the number of players from player-1.txt
num_players=$(head -n 1 "$filename")

# Start the MQTT publisher for each player in the background
for ((i = 1; i <= $num_players; i++)); do
    python3 pub.py "$i" "player-$i.txt" &
done

# Wait for all background processes to finish
wait
