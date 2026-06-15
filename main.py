import os
import json
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env")
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI in .env")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = mongo_client["cardiograph"]

# ──────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────

app = FastAPI(
    title="Disease Recommendation API",
    description="Generates lifestyle recommendations based on drug diagnosis and stores them in MongoDB.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Request model
# ──────────────────────────────────────────────
class RecommendationRequest(BaseModel):
    patient_id: str


# ──────────────────────────────────────────────
# OpenAI prompt
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are a clinical patient education assistant. Create a practical, CONCISE daily routine based on diagnosed conditions and prescribed drugs.

CRITICAL: Keep response SHORT and PRACTICAL. Max 3-5 bullet points per array. No lengthy paragraphs.

FIELD GUIDELINES:
- condition_summary: 1 sentence explaining the patient's situation
- daily_routine: Specific actionable steps for each time period (morning, afternoon, evening) — 3-5 items each
- diet_recommendations: Specific foods to eat (3-5 items)
- foods_to_limit: Specific foods to reduce/avoid (3-5 items)
- exercise_recommendations: Specific activities with frequency/duration (3-5 items)
- sleep_recommendations: Sleep hygiene practices (2-4 items)
- monitoring: What patient should track at home (3-5 items)
- avoid: Specific dangerous activities/habits (3-5 items)
- red_flags: Emergency symptoms requiring immediate medical attention (3-5 items)

Rules: No diagnosis, no medications, only lifestyle recommendations. Assume patient continues physician treatment.

Return STRICT JSON only with these exact fields."""


def generate_recommendation(diseases_info: str) -> dict:
    """Calls OpenAI to generate a lifestyle recommendation for the given diseases/drugs."""
    prompt = f"Generate concise lifestyle routine for a patient with the following conditions and prescribed drugs:\n{diseases_info}"

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw}


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────
@app.post("/recommend")
async def recommend(request: RecommendationRequest):
    """
    1. Fetch the patient's drug_diagnosis document by patientId.
    2. Generate a lifestyle recommendation via OpenAI.
    3. Upsert (insert or update) into disease_recommendation collection.
    """
    patient_id = request.patient_id

    # ── Step 1: Fetch drug diagnosis ──────────────────────────
    diagnosis = db["drug_diagnosis"].find_one({"patientId": patient_id})
    if not diagnosis:
        raise HTTPException(
            status_code=404,
            detail=f"No drug diagnosis found for patientId: {patient_id}",
        )

    # ── Step 2: Build a summary string of diseases & drugs ────
    disease_lines = []
    for key in ("id_1", "id_2", "id_3"):
        entry = diagnosis.get(key)
        if entry:
            drug = entry.get("Drug_Name", "N/A")
            disease = entry.get("Disease", "N/A")
            prob = entry.get("Probablity", entry.get("Probability", "N/A"))
            disease_lines.append(
                f"- Drug: {drug}, Disease: {disease}, Probability: {prob}"
            )

    if not disease_lines:
        raise HTTPException(
            status_code=404,
            detail=f"Drug diagnosis document for patientId {patient_id} has no entries.",
        )

    diseases_summary = "\n".join(disease_lines)

    # ── Step 3: Generate recommendation via OpenAI ────────────
    recommendation = generate_recommendation(diseases_summary)

    # ── Step 4: Extract suspected conditions ──────────────────
    suspected_conditions = []
    for key in ("id_1", "id_2", "id_3"):
        entry = diagnosis.get(key)
        if entry:
            disease = entry.get("Disease")
            if disease and disease not in suspected_conditions:
                suspected_conditions.append(disease)

    # ── Step 5: Upsert into disease_recommendation ────────────
    now = datetime.now(timezone.utc)

    result = db["disease_recommendation"].update_one(
        {"patientId": patient_id},
        {
            "$set": {
                "patientId": patient_id,
                "suspectedConditions": suspected_conditions,
                "recommendation": recommendation,
                "updatedAt": now,
            },
            "$setOnInsert": {
                "createdAt": now,
            },
        },
        upsert=True,
    )

    action = "updated" if result.matched_count > 0 else "created"

    return {
        "status": "success",
        "action": action,
        "patientId": patient_id,
        "suspectedConditions": suspected_conditions,
        "recommendation": recommendation,
    }


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)
