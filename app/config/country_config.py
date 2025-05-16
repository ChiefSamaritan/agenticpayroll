import json
import os

def load_country_config():
    current_dir = os.path.dirname(__file__)
    config_path = os.path.join(current_dir, "country_config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

country_config = load_country_config()