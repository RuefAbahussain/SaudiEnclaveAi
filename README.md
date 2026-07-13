# 🔐 Enclave — Local Meeting Summarizer 

## About

Enclave summarizes meetings entirely offline, transcription and AI summarization both run locally, with nothing sent to the cloud, designed for Saudi government organizations and any organization that requires full data privacy

=====================================

## Features

- Audio-to-text transcription: powered by OpenAI's Whisper (local, open-source)
- AI-generated summaries: key points, decisions made, and action items
- 100% local & private: no API keys, no external requests, works offline after setup
- Full transcript view: expand to read the raw transcription alongside the summary
- Simple drag-and-drop interface: no configuration needed from the end user

=====================================

## Tech Stack

- Backend: FastAPI (Python)
- Speech-to-Text: OpenAI Whisper (local, base model)
- Summarization: Ollama (e.g. `llama3.1`) via LiteLLM
- Frontend: Single-file HTML, CSS & vanilla JavaScript

=====================================

## Deploy / Run Locally

### 1. Prerequisites

- **ffmpeg** (required by Whisper):
  ```bash
  winget install ffmpeg
  ```

- **Ollama** installed and running with a model pulled:
  ```bash
  ollama serve
  ollama pull llama3.1
  ```

### 2. Run the backend

```bash
pip install -r requirements.txt
python main.py
```

The API will run at `http://localhost:8000`. Verify it's working at `http://localhost:8000/health`.

### 3. Run the frontend

Just open `index.html` directly in your browser — no build step required.

### Notes

- On first run, Whisper downloads the `base` model — this may take a moment depending on your connection.
- To use a different Ollama model, change `OLLAMA_MODEL` in `main.py`.
- Very long recordings (1hr+) may exceed some models' context window — consider a model with a larger context or add a chunking step for long transcripts.

=====================================

Built by Reoof Abahussain ★