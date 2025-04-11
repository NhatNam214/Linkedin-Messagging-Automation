import requests
import json
import time 

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CompanyScraper:
    def __init__(self, api_key, agent_id, companiesPerLaunch=1, 
                 spreadsheetUrl="", sessionCookie="", 
                 userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                 delayBetween=0, csvName="result",):
        self.api_key = api_key
        self.agent_id = agent_id
        self.companiesPerLaunch = companiesPerLaunch
        self.spreadsheetUrl = spreadsheetUrl    
        self.sessionCookie = sessionCookie
        self.userAgent = userAgent
        self.delayBetween = delayBetween
        self.csvName = csvName  
        self.base_url = 'https://api.phantombuster.com/api/v2/agents'
        self.headers = {
            'Content-Type': 'application/json',
            'x-phantombuster-key': self.api_key,
        }

    def launch_agent(self, companiesPerLaunch=10, delayBetween=2, csvName="result"):
        data = {
            "id": self.agent_id,
            "argument": {
                "companiesPerLaunch": companiesPerLaunch,
                "delayBetween": delayBetween,
                "csvName": csvName,
                "spreadsheetUrl": self.spreadsheetUrl,
                "sessionCookie": self.sessionCookie,
                "userAgent": self.userAgent,
                "delayBetween": self.delayBetween,
            }
        }
        
        response = requests.post(f'{self.base_url}/launch', headers=self.headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("Agent launched successfully.")
        else:
            print(f"Error: {response.status_code}, {response.text}")

