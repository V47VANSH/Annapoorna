from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import whisper
import os
from datetime import datetime
import shutil

router = APIRouter()
model = whisper.load_model("medium")

os.makedirs("backend/transcriptions", exist_ok=True)

@router.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = model.transcribe(temp_path)
        transcription = result["text"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = f"backend/transcriptions/transcription_{timestamp}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        os.remove(temp_path)

        return JSONResponse(
            content={"transcription": transcription, "file_path": txt_path},
            status_code=200
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.get("/download/")
async def download_file(file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/plain', filename=os.path.basename(file_path))
    return JSONResponse(content={"error": "File not found"}, status_code=404)
