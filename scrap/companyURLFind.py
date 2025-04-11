import requests
import json
import time 

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CompanyURLFinder:
    def __init__(self, api_key, agent_id, csvName = "result", market="en-US", spreadsheet_url="", numberOfLinesToProcess=1):
        self.api_key = api_key
        self.agent_id = agent_id
        self.csvName = csvName
        self.market = market
        self.spreadsheet_url = spreadsheet_url
        self.numberOfLinesToProcess = numberOfLinesToProcess    
        self.base_url = 'https://api.phantombuster.com/api/v2/agents'
        self.headers = {
            'Content-Type': 'application/json',
            'x-phantombuster-key': self.api_key,
        }

    def launch_agent(self):
        data = {
            "id": self.agent_id,
            "argument": {
                "csvName": self.csvName,
                "market": self.market,
                "spreadsheetUrl": self.spreadsheet_url,
                "numberOfLinesToProcess": self.numberOfLinesToProcess,
            }
        }
        
        response = requests.post(f'{self.base_url}/launch', headers=self.headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("Agent launched successfully.")
        else:
            print(f"Error: {response.status_code}, {response.text}")

    

