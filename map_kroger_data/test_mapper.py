import json
from mapper import map_kroger_to_zenday

with open("response-example.json") as f:
    kroger_data = json.load(f)["data"]

mapped = map_kroger_to_zenday(kroger_data)

print(json.dumps(mapped, indent=2))

