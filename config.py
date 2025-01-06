import json

def config():
    with open('config.json', 'r') as file:
        config = json.load(file)
    return config