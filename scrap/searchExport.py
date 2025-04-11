import requests
import json
import time 

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class SearchExport:
    def __init__(self, api_key = None, agent_id = None, 
                 category = "People", connectionDegreesToScrape = ["2","3+","1"],
                 numberOfLinesPerLaunch = 1, numberOfResultsPerLaunch = 1, 
                 numberOfResultsPerSearch = 1, searchType = "linkedInSearchUrl", 
                 enrichLeadsWithAdditionalInformation = True, linkedInSearchUrl = "", 
                 identityId = None, sessionCookie = None, columnName = "", 
                 inputColumnsToKeepInTheResult = [], 
                csvName = "result",removeDuplicateProfiles=False,watcherMode=False):
        self.api_key = api_key
        self.agent_id = agent_id
        self.category = category
        self.connectionDegreesToScrape = connectionDegreesToScrape
        self.numberOfLinesPerLaunch = numberOfLinesPerLaunch
        self.numberOfResultsPerLaunch = numberOfResultsPerLaunch
        self.numberOfResultsPerSearch = numberOfResultsPerSearch
        self.searchType = searchType
        self.enrichLeadsWithAdditionalInformation = enrichLeadsWithAdditionalInformation
        self.linkedInSearchUrl = linkedInSearchUrl
        self.identityId = identityId
        self.sessionCookie = sessionCookie
        self.columnName = columnName
        self.inputColumnsToKeepInTheResult = inputColumnsToKeepInTheResult
        self.removeDuplicateProfiles = removeDuplicateProfiles
        self.csvName = csvName
        self.watcherMode = watcherMode
        self.userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        self.base_url = 'https://api.phantombuster.com/api/v2/agents'
        self.headers = {
            'Content-Type': 'application/json',
            'x-phantombuster-key': self.api_key,
        }

    def launch_agent(self):
        data = {
            "id": self.agent_id,
            "argument": {
                "category": self.category,
                "connectionDegreesToScrape": self.connectionDegreesToScrape,
                "numberOfLinesPerLaunch": self.numberOfLinesPerLaunch,
                "numberOfResultsPerLaunch": self.numberOfResultsPerLaunch,
                "numberOfResultsPerSearch": self.numberOfResultsPerSearch,
                "searchType": self.searchType,
                "enrichLeadsWithAdditionalInformation": self.enrichLeadsWithAdditionalInformation,
                "linkedInSearchUrl": self.linkedInSearchUrl,
                "identityId": self.identityId,
                "sessionCookie": self.sessionCookie,
                "columnName": self.columnName,
                "inputColumnsToKeepInTheResult": self.inputColumnsToKeepInTheResult,
                "csvName": self.csvName,
                "removeDuplicateProfiles": self.removeDuplicateProfiles,
                "watcherMode": self.watcherMode,
                "userAgent": self.userAgent,
            }
        }
        
        response = requests.post(f'{self.base_url}/launch', headers=self.headers, data=json.dumps(data))
        if response.status_code == 200:
            print("Agent launched successfully.")
        else:
            print(f"Error: {response.status_code}, {response.text}")

