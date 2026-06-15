# Drug Routine Recommendation API

A FastAPI-based backend service that generates personalized lifestyle and routine recommendations for patients based on their drug diagnosis data. Powered by OpenAI and MongoDB.

## Features

- **AI-Powered Recommendations** — Generates concise, practical lifestyle routines using OpenAI (GPT-4o-mini) based on diagnosed conditions and prescribed drugs.
- **MongoDB Integration** — Fetches drug diagnosis data and upserts generated recommendations into the `disease_recommendation` collection.
- **Structured Output** — Returns condition summary, daily routines, diet recommendations, exercise plans, sleep guidance, monitoring tips, and red flags in strict JSON format.
- **Disease-Based Routine** — Standalone endpoint to generate routines directly from a disease name.

## Tech Stack

- **Framework**: FastAPI
- **AI**: OpenAI API (GPT-4o-mini)
- **Database**: MongoDB (Atlas)
- **Runtime**: Python 3.10+

## Getting Started

### 1. Clone the repository

```bash
git clone git@github.com:ahmedshayan112/Drug_routine_recommendation.git
cd Drug_routine_recommendation
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_connection_string
```

### 5. Run the server

```bash
python main.py
```

The API will be available at `http://localhost:7000`.

## API Endpoints

### `POST /recommend`

Generates a lifestyle recommendation for a patient based on their drug diagnosis.

**Request Body:**
```json
{
  "patient_id": "patient-uuid-here"
}
```

**Response:**
```json
{
  "status": "success",
  "action": "created",
  "patientId": "patient-uuid-here",
  "suspected_conditions": ["High Blood Pressure", "High Cholesterol"],
  "recommendation": {
    "condition_summary": "...",
    "daily_routine": { "morning": [], "afternoon": [], "evening": [] },
    "diet_recommendations": [],
    "foods_to_limit": [],
    "exercise_recommendations": [],
    "sleep_recommendations": [],
    "monitoring": [],
    "avoid": [],
    "red_flags": []
  }
}
```

### `POST /routine/from-disease`

Generates a lifestyle routine directly from a disease name (standalone, no DB lookup).

**Request Body:**
```json
{
  "disease": "Diabetes"
}
```

### `GET /health`

Health check endpoint — returns `{"status": "ok"}`.

## Project Structure

```
├── main.py               # Main FastAPI app with /recommend endpoint
├── disease_routine.py    # Standalone disease-based routine endpoint
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not tracked)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## License

This project is for internal/educational use.
