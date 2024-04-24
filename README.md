# MQTT Board Game

This repo contains the Python source code for running an MQTT board game using
HiveMQ as the MQTT broker.

## Running

Start the HiveMQ broker.

```bash
./path/to/hivemq-<VERSION>/bin/run.sh
```

Then, ensure that the game `.txt` files are located in the same directory as
`player.py` and `run.sh`. Run the following command to start the game.

```bash
chmod a+x ./run.sh
./run.sh
```
