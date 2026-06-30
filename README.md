# Candidate Data Transformer

## Overview

The Candidate Data Transformer is a full-stack web application that consolidates candidate information from multiple input sources into a single unified candidate profile. The system extracts candidate data from CSV files, ATS JSON files, and PDF resumes, normalizes the data, removes duplicate records, merges candidate information, calculates an overall confidence score, and generates the final candidate profile using either a default or custom output schema.


## Features

- Import candidate data from CSV files
- Parse ATS JSON files
- Extract information from PDF resumes
- Normalize candidate information
- Match candidates using Email, Phone, and Name
- Remove duplicate candidate records
- Merge data using source priority
- Calculate Overall Confidence Score
- Generate Default Output Schema
- Generate Custom Output Schema
- Download final profile as JSON and CSV


## Technology Stack

- **Frontend**: React.js, Tailwind CSS, Vite
- **Backend**: Python, Flask
- **PDF Parsing**: PyMuPDF
- **DOCX Parsing**: python-docx
- **Regular Expressions**: for resume field extraction


## Project Structure

project/
│
├── input/
│   ├── candidates.csv
│   ├── ats.json
│   ├── config.json
│   └── Deepika_Resume.pdf
│
├── backend/
│   ├── app.py
│   ├── routes.py
│   ├── routes_schema.py
│   ├── requirements.txt
│   ├── models/
│   ├── parsers/
│   ├── services/
│   └── utils/
│
└── candidate-transformer/   ← React Frontend
    ├── src/
    └── package.json


## Processing Pipeline

Input Sources
     ↓
Data Extraction
     ↓
Candidate Matching
     ↓
Normalization
     ↓
Deduplication
     ↓
Merge Records
     ↓
Conflict Resolution
     ↓
Overall Confidence Score
     ↓
Output Schema Selection
     ↓
Generate Final Profile


## Source Priority

1. Resume
2. ATS JSON
3. CSV


## Candidate Matching Priority

1. Email
2. Phone
3. Full Name


## Input Files

The application accepts the following input sources:

- CSV file
- ATS JSON file
- PDF Resume
- Config JSON (Optional)

## Output

The application generates:

- Unified Candidate Profile
- Overall Confidence Score
- Default Output Schema
- Custom Output Schema
- Downloadable JSON
- Downloadable CSV

## Edge Cases Handled

- No output schema selected
- No fields selected in custom schema
- Invalid fields in custom schema
- Duplicate fields in custom schema
- Missing values in selected fields

## How to Run

1. Clone the repository.

```bash
git clone https://github.com/Deepika4825/Candidate_Data_Transfer.git
```

2. Install backend dependencies.

```bash
cd backend
pip install -r requirements.txt
```

3. Run the Flask backend.

```bash
python app.py
```

4. Install frontend dependencies.

```bash
cd candidate-transformer
npm install
```

5. Run the React frontend.

```bash
npm run dev
```



