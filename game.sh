#!/bin/bash

# Constant filename for player 1
filename="player-1.txt"

# Read the number of players from player-1.txt
num_players=$(head -n 1 "$filename")

# Start the MQTT publisher for each player
for ((i = 1; i <= $num_players; i++)); do
    gnome-terminal -- bash -c "python3 pub.py $i 'player-$i.txt'; exec bash" &
done
wait
