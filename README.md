# Candidate Data Transformer

A full-stack web application that extracts, normalizes, deduplicates, merges, and scores candidate profiles from multiple data sources into a single unified output.

## Tech Stack

- **Frontend**: React 19 + Tailwind CSS v4 + Vite
- **Backend**: Python Flask

## Pipeline

```
Input Sources
    ↓ Parsing & Extraction
    ↓ Candidate Matching (email → phone → name)
    ↓ Normalization
    ↓ Deduplication
    ↓ Merge
    ↓ Conflict Resolution
    ↓ Confidence Scoring
    ↓ Output Schema Generation
    ↓ Export (JSON / CSV)
```

## Input Sources

- Recruiter CSV (`candidates.csv`)
- ATS JSON (`ats.json`)
- Resume PDF/DOCX (`Deepika_Resume.pdf`)
- Runtime Config JSON (`config.json`)

## Project Structure

```
├── backend/
│   ├── app.py
│   ├── routes.py
│   ├── routes_schema.py
│   ├── models/
│   ├── parsers/
│   ├── services/
│   └── utils/
├── candidate-transformer/   ← React frontend
├── input/                   ← Sample input files
└── README.md
```

## Running the Application

**Backend (Flask):**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Frontend (React):**
```bash
cd candidate-transformer
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## Confidence Score Formula

| Component | Points |
|---|---|
| Resume present | +40 |
| ATS JSON present | +30 |
| CSV present | +20 |
| Fields confirmed by 2+ sources (×3 each) | up to +12 |
| Profile completeness (×2 each field) | up to +14 |
| Conflict penalty (×4 each) | deducted |
