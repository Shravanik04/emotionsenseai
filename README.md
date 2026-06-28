# Multilingual Emotion & Sentiment Analyzer Platform

An enterprise-grade, real-time AI platform that performs multilingual sentiment classification, multi-emotion detection, sarcasm classification, readability indexing, and entity recognition. The system is designed to process and analyze text as you type, providing insights in under 300ms.

---

## 🌟 Key Features

* **Real-time Engine**: Continuous debounced analysis (400ms) over a persistent WebSocket connection. No analyze button needed.
* **Dual Sentiment & Emotion Models**: Evaluates text using:
  * Multilingual Sentiment: `cardiffnlp/twitter-xlm-roberta-base-sentiment`
  * English Emotion: `j-hartmann/emotion-english-distilroberta-base`
* **Dedicated Sarcasm Pipeline**: Utilizes `dima806/sarcasm-detection-distilbert` along with rule-based syntactic clash heuristics to identify sarcasm and contextually invert false positive sentiments to negative frustration/disappointment.
* **Enriched 45+ Sub-Emotion Categories**: Refines standard transformer predictions into detailed emotion classes using mapped keyword lexicons. Recently expanded to include `belonging`, `collaboration`, `fatigue`, and `discomfort`.
* **Contextual Emotion Enrichment**: Automatically detects semantic patterns (such as combining positive collaboration context like "love" + "team", or physical aversion like "hate" + "waking up early") to dynamically trigger and boost secondary emotions above the visibility threshold.
* **Premium Tabbed Results Layout**: Replaced the long vertical-scrolling results panel with a custom, glassmorphic Tab Bar component:
  * **Overview**: Sarcasm alert banner, Sentiment distribution bars, Primary Emotion radial gauge, and AI Insights.
  * **Emotions**: Secondary detected emotions (exceeding 20% score) with single-sentence contextual explanations, and a ranked emotion distribution chart.
  * **Sentences**: Flow timeline of sentence-by-sentence emotions and an interactive breakdown table highlighting sentiment, emotion, and sarcasm.
  * **Metadata & Entities**: Language detection, Named Entity Recognition (NER), and a dynamic Word Cloud.
* **Visual Copy Feedback**: Real-time copy confirmation on the "Copy Report" button, which turns positive green and shows "Copied!" for 2 seconds.
* **Theme-Adaptive High Visibility**: Fully optimized colors for both dark and light modes. Custom-designed CSS variables and adaptive Tailwind classes ensure that all headers, text paragraphs, tags, and charts remain dark and highly legible in light mode while transitioning to high-contrast glowing elements in dark mode.
* **Multilingual Input & Translation**: Offline Unicode script range detection for Indian languages (Hindi, Kannada, Telugu, Tamil, Malayalam, Bengali, Gujarati, Punjabi) with Google Translate API fallbacks.
* **Voice Capabilities**: Browser-native Speech-to-Text (Microphone recording) and Text-to-Speech (reading insights aloud).
* **Automatic DB Sync**: Automatically commits every real-time analysis to the SQLite database without manual saving.
* **Export Utilities**: Quick file exports to **CSV**, **JSON**, and print-ready **PDF** with print-optimized CSS rules.
* **High-Speed Batch Analysis**: Upload and bulk-analyze plain text (`.txt`), CSV (`.csv`), and Excel (`.xlsx`, `.xls`) files.
  * **Robust File Support**: Reads various encodings (UTF-8, UTF-8-SIG, Latin-1, CP1252, UTF-16) and Excel workbook spreadsheet versions (`openpyxl` & `xlrd` engines).
  * **Flexible Headers**: Employs substring matching and keyword expansion to locate review columns (falls back to a single-column or first column if headers are missing or custom).
  * **Optimized Concurrency**: Processes batch runs concurrently via an `asyncio.Semaphore(10)` limit, delivering a 3x to 5x speedup without overloading CPU cores.
  * **Google Translate Bypass**: Automatically skips translation network calls for English rows to bypass latency and avoid API rate limits.
  * **Redesigned UI & Download**: Features a split side-by-side pie chart and detailed frequency list (avoiding legend overlap) and triggers programmatic downloads with dynamic button status feedback.

---

## 📂 Project Structure

```bash
ss-basic/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py             # REST, WebSocket & export endpoints
│   │   ├── core/
│   │   │   └── config.py             # Hugging Face models & settings
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py            # SQLite engine & sessions
│   │   ├── models/
│   │   │   └── sentiment_model.py    # SQLAlchemy tables schema
│   │   ├── schemas/
│   │   │   └── sentiment.py          # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── analysis_service.py   # Multi-sentence NLP model engine
│   │   │   └── sarcasm_service.py    # Hybrid sarcasm detection logic
│   │   ├── utils/
│   │   │   ├── emotion_lexicon.py    # Sub-emotions, emojis & context boosters
│   │   │   ├── keyword_utils.py      # Keyword extractor
│   │   │   └── insight_utils.py      # AI explanations and text templates
│   │   └── main.py                   # FastAPI app & SQLite migrator
│   └── tests/
│       ├── test_api.py               # REST route checks
│       └── test_sarcasm.py           # Sarcasm, readability & NER tests
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── AnalyzeText.tsx       # Live STT/TTS dashboard with timeline
    │   │   ├── History.tsx           # CSV/JSON/PDF exports and search lists
    │   │   └── Dashboard.tsx         # Analytical statistics overview
    │   ├── services/
    │   │   └── api.ts                # Axios wrappers & WebSocket builders
    │   ├── types/
    │   │   └── index.ts              # TypeScript interfaces
    │   └── index.css                 # Base theme and print media queries
```

---

## 🚀 Setup & Launch

### 1. Backend Server Setup
From the repository root, run:
```powershell
# Navigate into backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\activate

# Start uvicorn development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The server will start on `http://localhost:8000`. The first run will automatically download the required Hugging Face weights (~500MB) to your local cache directory.

---

### 2. Frontend React Dashboard Setup
In a new terminal window:
```powershell
# Navigate into frontend directory
cd frontend

# Install node modules
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

To run the backend test suite, activate your virtual environment in `backend/` and run:
```powershell
pytest
```
This runs 12 comprehensive unit tests verifying sarcasm classification, sentiment flipping, readability indices, named entities, custom file headers, Excel sheet processing, and concurrent batch analysis.

To run TypeScript verification:
```powershell
cd frontend
npx.cmd tsc --noEmit
```
