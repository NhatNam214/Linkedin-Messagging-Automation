import requests
import pandas as pd
import io

import os
import csv
import uuid
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
load_dotenv()
import time
from JSONResponse import JSONResponse

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def getCSV(url: str, columns: list[str] = None) ->str:
    # Download the file from the provided URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for failed requests

    # Read CSV content directly from response without writing to a temporary file
    df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8")
    return df[columns]
def phantom_fetch_output(id: str, api_key: str) -> str:
        url = f"https://api.phantombuster.com/api/v2/agents/fetch-output?id={id}"
        headers = {
            "accept": "application/json",
            "X-Phantombuster-Key": api_key
        }
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', '')
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

def load_credentials_and_service():
    """
    Load credentials and initialize the Google Sheets API service.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build("sheets", "v4", credentials=creds)
    return service

def get_existing_queries(service, spreadsheet_id, sheet_name):
    """
    Get the list of existing queries from the sheet (case-insensitive).
    """
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!B:B"
        ).execute()
        values = result.get("values", [])
        existing_queries = {row[0].strip().lower() for row in values if row}
        return existing_queries
    except HttpError as error:
        return [f"Error occurred while fetching existing queries: {error}"]

def append_new_queries(service, spreadsheet_id, sheet_name, new_queries):
    """
    Append new queries to the sheet.
    """
    if not new_queries:
        return ["No new queries to append."]
    
    values = [[str(uuid.uuid4()), query, "", "", "", "", "", "", "", "", 0] for query in new_queries]
    body = {"values": values}
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:K",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return [f"Appended {result.get('updates').get('updatedRows')} new rows to the sheet."]
    except HttpError as error:
        return [f"Error occurred while appending new queries: {error}"]

def push_csv_to_sheets(csv_file_path, spreadsheet_id, sheet_name):
    """
    Read a CSV file and push non-duplicate queries to Google Sheets.
    """
    messages = []
    service = load_credentials_and_service()
    if not service:
        return ["Failed to initialize Google Sheets API service."]
    
    existing_queries = get_existing_queries(service, spreadsheet_id, sheet_name)
    if isinstance(existing_queries, list):  # Error message was returned
        return existing_queries
    
    new_queries = []
    duplicate_queries = []

    try:
        with open(csv_file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                query = row.get("query", "").strip()
                if query:
                    if query.lower() in existing_queries:
                        duplicate_queries.append(query)
                    else:
                        new_queries.append(query)
    except FileNotFoundError:
        return [f"File '{csv_file_path}' not found."]
    except Exception as e:
        return [f"Error while reading the CSV file: {e}"]
    
    result_messages = append_new_queries(service, spreadsheet_id, sheet_name, new_queries)
    messages.extend(result_messages)

    if duplicate_queries:
        messages.append("The following queries were duplicates and were not added:")
        messages.extend([f"- {q}" for q in duplicate_queries])
    else:
        messages.append("No duplicate queries found.")

    return "\n".join(messages)
def get_rows_as_json(spreadsheet_id, sheet_name, num):
    """
    Get the first `num` rows from the Google Sheet (excluding the header) and return them as JSON objects.
    """
    try:
        service = load_credentials_and_service()
        if not service:
            return "Failed to initialize Google Sheets API service."

        # Get all data including headers
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}"
        ).execute()

        values = result.get("values", [])
        if not values:
            return "No data found in the sheet."

        header = values[0]
        data_rows = values[1:num + 1]  # Exclude header, get top `num` rows

        # Convert rows to list of dictionaries
        json_data = [dict(zip(header, row)) for row in data_rows]
        return json_data

    except HttpError as error:
        return f"Error occurred while reading data from the sheet: {error}"

def fetch_row_by_id(spreadsheet_id: str, sheet_name: str, target_id: str) -> JSONResponse | None:
    """
    Truy xuất dòng từ Google Sheets theo ID và trả về dưới dạng JSONResponse.
    """
    service = load_credentials_and_service()
    if not service:
        return None

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_name
        ).execute()

        values = result.get("values", [])
        if not values:
            return None

        headers = values[0]
        rows = values[1:]

        id_index = headers.index("id") if "id" in headers else -1
        if id_index == -1:
            return None

        for row in rows:
            if len(row) > id_index and row[id_index].strip() == target_id.strip():
                row_dict = dict(zip(headers, row))
                return JSONResponse(
                    id=row_dict.get("id", ""),
                    query=row_dict.get("query", ""),
                    companyName=row_dict.get("companyName", ""),
                    companyID=row_dict.get("companyID", ""),
                    companyUrl=row_dict.get("companyUrl", ""),
                    description=row_dict.get("description", ""),
                    fullName=row_dict.get("fullName", ""),
                    jobTitle=row_dict.get("jobTitle", ""),
                    profileUrl=row_dict.get("profileUrl", ""),
                    outreachMessage=row_dict.get("outreachMessage", ""),
                    status=int(row_dict.get("status", 0)) if row_dict.get("status", "0").isdigit() else 0
                )

        return None  # Không tìm thấy
    except Exception as e:
        print(f"❌ Error while fetching row by ID: {e}")
        return None
    
def update_by_id(sheets_id: str, sheets_name: str, target_id: str, json_data: JSONResponse):
    service = load_credentials_and_service()
    if not service:
        return False

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheets_id,
            range=sheets_name
        ).execute()

        values = result.get("values", [])
        if not values:
            print("❌ Sheet has no data or headers.")
            return False

        headers = values[0]
        rows = values[1:]

        id_index = headers.index("id")
        status_index = headers.index("status")
        query_index = headers.index("query")

        for i, row in enumerate(rows):
            if len(row) <= id_index:
                continue

            if row[id_index].strip() == str(target_id).strip():
                all_empty = True
                current_status = row[status_index].strip() if status_index < len(row) else ""

                new_data = [
                    json_data.id,
                    json_data.query,
                    json_data.companyName,
                    json_data.companyID,
                    json_data.companyUrl,
                    json_data.description,
                    json_data.fullName,
                    json_data.jobTitle,
                    json_data.profileUrl,
                    json_data.outreachMessage,
                    str(json_data.status),
                ]

                # Pad if shorter than headers
                if len(new_data) < len(headers):
                    new_data += [""] * (len(headers) - len(new_data))

                range_to_update = f"{sheets_name}!A{i + 2}"
                body = {"values": [new_data]}

                service.spreadsheets().values().update(
                    spreadsheetId=sheets_id,
                    range=range_to_update,
                    valueInputOption="RAW",
                    body=body
                ).execute()

                print("✅ Row updated")
                return True

        print("⚠️ No matching or updatable row found")
        return False

    except Exception as e:
        print(f"❌ Error updating sheet: {e}")
        return False
    

    
