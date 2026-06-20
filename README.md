# SentimentScope - AI-Powered Sentiment Analyzer

SentimentScope is a modern, full-stack AI application designed to analyze the sentiment of textual data. It leverages a fine-tuned **DistilBERT** transformer model to classify text into positive or negative sentiment with high confidence scores, providing visual analytics via a responsive React dashboard.

## 🚀 Features

- **Single Text Analysis**: Get real-time sentiment classifications (Positive/Negative) and confidence scores for any input text.
- **Bulk CSV Upload**: Upload files containing multiple text items (up to 500 rows) and process them in batch.
- **Dynamic Analytics Dashboard**: Visualize historical data, sentiment trends, and statistics using modern interactive charts (**Recharts**).
- **History Tracker**: Persistently store and manage past analyses in a local SQLite database.
- **Clean Responsive UI**: Designed with React, TypeScript, and styled with Tailwind CSS, supporting dark/light mode aesthetics.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML Model**: `distilbert-base-uncased-finetuned-sst-2-english` (Hugging Face Transformers / PyTorch)
- **Database**: SQLite (SQLAlchemy ORM)
- **Caching & Processing**: Pandas

### Frontend
- **Framework**: React 18 with Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS & PostCSS
- **Icons**: Lucide React
- **Charts**: Recharts

---

## ⚙️ Project Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

---

### 1. Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Windows (CMD)
   .\venv\Scripts\activate.bat

   # macOS/Linux
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the `backend/` directory (if not already present):
   ```env
   DATABASE_URL=sqlite:///./sentiment.db
   CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:3000
   MAX_CSV_ROWS=500
   ```
   *Note: If your frontend dev server runs on another port (like `5174`), ensure it is added to `CORS_ORIGINS`.*

5. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   *The backend will be running at `http://localhost:8000`. You can inspect the automatic API documentation at `http://localhost:8000/docs`.*

---

### 2. Frontend Setup

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install the package dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the `frontend/` directory (if not already present):
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

4. Start the development server:
   ```bash
   # On standard command prompt/bash:
   npm run dev

   # On Windows PowerShell (if script execution is disabled):
   npm.cmd run dev
   ```
   *The frontend will run at `http://localhost:5173` (or `http://localhost:5174` if `5173` is already in use).*

---

## 📁 Directory Structure

```text
sentimentscope/
├── backend/
│   ├── app/
│   │   ├── api/            # API endpoints & routing
│   │   ├── core/           # Config and settings
│   │   ├── db/             # Database session & models setup
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic schemas (request/response validation)
│   │   ├── services/       # AI sentiment analyzer and database operations
│   │   └── main.py         # Entry point for FastAPI application
│   ├── requirements.txt    # Python packages
│   └── sentiment.db        # SQLite database file (auto-generated)
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable layout and UI components
│   │   ├── pages/          # Dashboard, AnalyzeText, UploadCSV, Stats, History
│   │   ├── App.tsx         # Root component & Router configuration
│   │   └── main.tsx        # Vite entry point
│   ├── package.json
│   └── vite.config.ts
└── .gitignore              # Ignored folders (venv, node_modules, secrets)
```

---

## 🧪 Running Tests

To run backend tests, use `pytest` within the active backend virtual environment:
```bash
cd backend
pytest
```

---

## 🌐 Deployment

For instructions on deploying the full-stack app (FastAPI + React) to production platforms like **Render**, **Vercel**, or **Railway**, see the deployment guide in your codebase notes.
