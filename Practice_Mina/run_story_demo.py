import json
import pyttsx3
import time

engine = pyttsx3.init()

import json
import pyttsx3
import time
from pathlib import Path

engine = pyttsx3.init()

current_folder = Path(__file__).parent
story_file = current_folder / "my_first_story.json"

with open(story_file, "r", encoding="utf-8") as file:
    story = json.load(file)

for dialog in story:
    print("Running dialog:", dialog["id"])

    for move in dialog["moves"]:
        if move["type"] == "say":
            text = move["text"]
            print("Robot says:", text)
            engine.say(text)
            engine.runAndWait()
            time.sleep(1)

for dialog in story:
    print("Running dialog:", dialog["id"])

    for move in dialog["moves"]:
        if move["type"] == "say":
            text = move["text"]
            print("Robot says:", text)
            engine.say(text)
            engine.runAndWait()
            time.sleep(1)