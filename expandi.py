import requests
from dotenv import load_dotenv
load_dotenv()
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def send_messages(profile_link, first_name: str | None = None, company_name: str | None = None, custom_placeholder: str | None = None):
    url = "https://api.liaufa.com/api/v1/open-api/campaign-instance/676642/assign/"
    params = {
        "key": os.getenv("EXPANDING_API_KEY"),
        "secret": os.getenv("EXPANDING_API_SECRET")
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = { 
        "profile_link": profile_link,   
        "first_name": first_name, 
        "company_name": company_name, 
        "custom_placeholder": custom_placeholder 
    }
    response = requests.post(url, params=params, headers=headers, json=data)
    return response.json()
