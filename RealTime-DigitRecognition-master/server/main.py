from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import cv2
import numpy as np
import os
from .digit_service import extract_digits_from_frame
from .excel_service import ExcelService

app = FastAPI(title="Mark Scanner API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    image_b64: str
    excel_path: str = "marks.xlsx"

@app.get("/")
def read_root():
    return {"status": "Mark Scanner API is running"}

@app.post("/scan")
def scan_frame(payload: ScanRequest):
    try:
        # Decode base64 image
        header, _, data = payload.image_b64.partition(",")
        if not data: data = header
        
        img_bytes = base64.b64decode(data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # Process with CNN Digit Service
        results = extract_digits_from_frame(frame)
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
def save_marks(payload: ScanRequest):
    try:
        # Same decode logic
        header, _, data = payload.image_b64.partition(",")
        if not data: data = header
        
        img_bytes = base64.b64decode(data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Get digits
        results = extract_digits_from_frame(frame)
        marks = [r["digit"] for r in results]
        
        if not marks:
            return {"success": False, "message": "No digits detected"}

        # Save to Excel
        total = ExcelService.create_or_append_marks(payload.excel_path, marks)
        grand_total = ExcelService.get_grand_total(payload.excel_path)
        
        return {
            "success": True,
            "marks": marks,
            "row_total": total,
            "grand_total": grand_total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
