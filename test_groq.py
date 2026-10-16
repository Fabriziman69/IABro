import os
import requests
from dotenv import load_dotenv

load_dotenv()
r = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {os.environ.get("GROQ_API_KEY")}'})
print([m['id'] for m in r.json().get('data', [])])
