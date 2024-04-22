import sys
import random

def generate_coordinates():
    return random.randint(0, 500), random.randint(0, 500), random.randint(0, 1)

def generate_match_data(num_rounds):
    match_data = []
    for _ in range(num_rounds):
        round_data = [generate_coordinates() for _ in range(2)]
        match_data.append(round_data)
    return match_data

def write_match_data_to_file(match_data, player_num,num_players):
    filename = f"player_{player_num}.txt"
    with open(filename, 'w') as file:
        file.write(f"{num_players}\n")
        for round_data in match_data:
            for coords in round_data:
                file.write(' '.join(map(str, coords)) + '\n')
    print(f"Data written to {filename}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <num_players>")
        sys.exit(1) 
    
    num_players = int(sys.argv[1])
    
    for player_num in range(1, num_players + 1):
        num_rounds = 5  # Number of rounds per player
        match_data = generate_match_data(num_players)
        write_match_data_to_file(match_data, player_num,num_players)
