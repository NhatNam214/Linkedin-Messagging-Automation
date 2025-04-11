from pydantic import BaseModel

class JSONResponse(BaseModel):
    id: str
    query: str
    companyName: str
    companyID: str
    companyUrl: str
    description: str
    fullName: str
    jobTitle: str
    profileUrl: str 
    outreachMessage: str
    status: int # 0: Naive, 1: Not Sent, 2: Sent, 3: Failed, 4: Success