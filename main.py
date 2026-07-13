import os               
import shutil           
import tempfile         
import logging           

import whisper          
from litellm import completion   

from fastapi import FastAPI, File, UploadFile, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse  

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger("meeting-summarizer")   



WHISPER_MODEL_NAME = "base"

OLLAMA_MODEL = "ollama/qwen2.5:3b"

OLLAMA_API_BASE = "http://localhost:11434"

ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg", ".mpga", ".mpeg"}

MAX_FILE_SIZE_MB = 200

SUMMARY_PROMPT = """You are an assistant that writes clean, structured meeting summaries.Write the summary in the exact same language as the transcript. 
Do not translate it into a different language.

Given the raw transcript of a meeting below, produce:

1. **Summary** — a short paragraph (3-5 sentences) capturing the purpose and outcome of the meeting.
2. **Key Points** — bullet list of the main discussion points.
3. **Decisions Made** — bullet list (write "None" if none were made).
4. **Action Items** — bullet list in the form: [Owner] Task (if owner is unclear, write "Unassigned").

Respond in the same language as the transcript.
Write the summary in the exact same language as the transcript. 
Do not translate it into a different language.

Transcript:
\"\"\"
{transcript}
\"\"\"
"""

app = FastAPI(title="Smart Meeting Summarizer (Local AI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_methods=["*"],  
    allow_headers=["*"],  
)

logger.info(f"Loading Whisper model '{WHISPER_MODEL_NAME}'...")
whisper_model = whisper.load_model(WHISPER_MODEL_NAME)
logger.info("Whisper model loaded.")


def transcribe_audio(file_path: str) -> str:
    result = whisper_model.transcribe(file_path)
    return result["text"].strip()


def summarize_text(transcript: str) -> str:
    prompt = SUMMARY_PROMPT.format(transcript=transcript)

    response = completion(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        api_base=OLLAMA_API_BASE,
    )

    return response["choices"][0]["message"]["content"].strip()


@app.get("/health")
def health_check():
    
    return {"status": "ok", "whisper_model": WHISPER_MODEL_NAME, "ollama_model": OLLAMA_MODEL}


@app.post("/summarize")
async def summarize_meeting(file: UploadFile = File(...)):
   
    ext = os.path.splitext(file.filename)[1].lower()   
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    tmp_dir = tempfile.mkdtemp()                        
    tmp_path = os.path.join(tmp_dir, file.filename)       

    try:
       
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB.",
            )

        logger.info(f"Transcribing '{file.filename}' ({size_mb:.1f} MB)...")
        transcript = transcribe_audio(tmp_path)

        if not transcript:
            raise HTTPException(status_code=422, detail="Transcription returned empty text. Check the audio file.")

        logger.info("Summarizing transcript with local Ollama model...")
        summary = summarize_text(transcript)

        return JSONResponse({
            "filename": file.filename,
            "transcript": transcript,   
            "summary": summary,
        })

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Error processing meeting file")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
