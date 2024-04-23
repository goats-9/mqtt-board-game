#!/bin/bash

# Constant filename for player 1
filename="player-1.txt"

# Read the number of players from player-1.txt
num_players=$(head -n 1 "$filename")

# Start the MQTT publisher for each player in the background
for ((i = 1; i <= $num_players; i++)); do
    python3 player.py -n $i & pid=$!
    echo "Process \"$i\" started";
    PID_LIST+=" $pid";
done

trap "kill $PID_LIST" SIGINT

echo "Parallel processes have started";

wait $PID_LIST

echo
echo "All processes have completed";