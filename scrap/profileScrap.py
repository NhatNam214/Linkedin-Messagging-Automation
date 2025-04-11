import requests
import json
import time 

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class ProfileScrapper:
    def __init__(self, agent_id, api_key, session_cookie, user_agent, spreadsheet_url):
        self.agent_id = agent_id
        self.api_key = api_key
        self.session_cookie = session_cookie
        self.user_agent = user_agent
        self.spreadsheet_url = spreadsheet_url
        self.base_url = 'https://api.phantombuster.com/api/v2/agents'
        self.headers = {
            'Content-Type': 'application/json',
            'x-phantombuster-key': api_key,
        }

    def launch_agent(self, number_of_adds=1, enrich_with_company=False, push_to_crm=True, identity_id=None):
        data = {
            "id": self.agent_id,
            "argument": {
                "numberOfAddsPerLaunch": number_of_adds,
                "enrichWithCompanyData": enrich_with_company,
                "pushResultToCRM": push_to_crm,
                "spreadsheetUrl": self.spreadsheet_url,
                "identityId": identity_id,
                "sessionCookie": self.session_cookie,
                "userAgent": self.user_agent
            }
        }
        
        response = requests.post(f'{self.base_url}/launch', headers=self.headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("Agent launched successfully.")
        else:
            print(f"Error: {response.status_code}, {response.text}")

    def fetch_output(self):
        while True:
            response = requests.get(f"{self.base_url}/fetch-output?id={self.agent_id}", headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', '')

                print(f"Current status: {status}")

                if status == "running":
                    print("Agent is still running... Waiting for completion.")
                    time.sleep(10)  # Đợi 10 giây rồi thử lại
                    continue

                output_text = result.get('output', '')
                csv_url = None

                for word in output_text.split():
                    if word.startswith("https://") and word.endswith(".csv"):
                        csv_url = word
                        break

                return csv_url
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None

