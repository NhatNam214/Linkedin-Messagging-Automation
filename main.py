from fastapi import FastAPI, Query, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from JSONResponse import JSONResponse
import pandas as pd

from scrap.scrapping import crawl_generate
from utils import update_by_id, fetch_row_by_id, push_csv_to_sheets, get_rows_as_json
from expandi import send_messages
from dotenv import load_dotenv
load_dotenv()
import uvicorn
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def safe_str(val):
    if pd.isna(val):
        return ""
    return str(val)
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    fpt = file.filename
    print(fpt)
    try:
        with open(fpt, "wb") as f:
            f.write(file.file.read())
        csv_file_path = "result.csv"
        spreadsheet_id = "1I60db7GVpq13Q-845-pQRdQFwr55zkdGTIdf6YyVBek"
        sheet_name = "outreachMessages"
        message = push_csv_to_sheets(csv_file_path, spreadsheet_id, sheet_name)
        print(message)
        return {"message": f"{message}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/get", response_model=list[JSONResponse])
async def get(limit: int = Query(10, ge=1)):
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME")
    datas = get_rows_as_json(spreadsheet_id, sheet_name, limit)
    return datas
@app.post("/generate")
async def generate():
    try:
        spreadsheet_id = os.getenv("SPREADSHEET_ID")
        sheet_name = os.getenv("SHEET_NAME")
        datas = get_rows_as_json(spreadsheet_id, sheet_name, 10)
        datas = [row for row in datas if str(row.get("status", "")).strip() == "0"]
        if not datas:
            raise HTTPException(status_code=404, detail="No data found in the sheet.")
        for data in datas:
            query = data.get("query")
            id = data.get("id")
            response = crawl_generate(query, id)
            print("response", response)
            # Update the status in the sheet based on the response
            #Code here to update the status in the sheet
            sheets_id = os.getenv("SPREADSHEET_ID")
            sheet_name = os.getenv("SHEET_NAME")
            isSuccess = update_by_id(sheets_id=sheets_id, sheets_name=sheet_name, target_id=id, json_data=response)
            if not isSuccess:
                raise HTTPException(status_code=500, detail="Failed to update the sheet.")
            return {"message": "Data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Data generated successfully"}
@app.post("/send")
async def send(id: str = Query(...)):
    try:
        # Lấy dữ liệu từ Google Sheets
        data_obj = fetch_row_by_id(
            os.getenv("SPREADSHEET_ID"),
            os.getenv("SHEET_NAME"),
            id
        )
        if not data_obj:
            raise HTTPException(status_code=404, detail="Data not found.")

        # Chuyển thành dict để xử lý
        data = data_obj.model_dump()

        # Gửi tin nhắn
        respone = send_messages(
            profile_link=data.get("profileUrl"),
            first_name=data.get("fullName"),
            company_name=data.get("companyName"),
            custom_placeholder=data.get("outreachMessage"),
        )
        print("respone", respone)
        respone = JSONResponse(
            id=id,
            query=data["query"],
            companyName=safe_str(data["companyName"]),
            companyID=safe_str(data["companyID"]),
            companyUrl=safe_str(data["companyUrl"]),
            description=safe_str(data["description"]),
            fullName=safe_str(data["fullName"]),
            jobTitle=safe_str(data["jobTitle"]),
            profileUrl=safe_str(data["profileUrl"]),
            outreachMessage=safe_str(data["outreachMessage"]),
            status=2,
        )
        isSuccess = update_by_id(sheets_id=os.getenv("SPREADSHEET_ID"), sheets_name=os.getenv("SHEET_NAME"), target_id=id, json_data=respone)
        if not isSuccess:
            raise HTTPException(status_code=500, detail="Failed to update the sheet.")
        return {"message": "Data updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ {str(e)}")

    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)