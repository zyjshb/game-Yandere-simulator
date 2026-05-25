lines = open('yandere_game.py', errors='ignore').read().splitlines()
for idx, line in enumerate(lines[:110]):
    print(f"{idx+1}: {line}")
