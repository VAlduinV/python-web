import json
import requests

data = {
            "name": "Alduin",
            "description": "Testing",
            "done": True
        }

headers = {'Content-type': 'application/json'}

response = requests.post('http://127.0.0.1:8800/api/notes_info',
                         data=json.dumps(data), headers=headers)

print(response.json())


