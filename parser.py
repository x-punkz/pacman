import json


class Parser:
    # def __init__(self) -> None:
    with open("config.json") as file:
        data = json.load(file)
    print(data)
