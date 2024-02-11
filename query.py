#Portions copyright langchain, ray project, and their respective holders. All other portions copyright 2024 Christian Mirra
import sys

import requests

query = sys.argv[1]
response = requests.post(f"http://localhost:8000/?query={query}")
print(response.content.decode())
