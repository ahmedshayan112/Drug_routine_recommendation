import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(title="Disease-Based Routine API")

class DiseaseRequest(BaseModel):
    disease: str

SYSTEM_PROMPT = """You are a clinical patient education assistant. Create a practical, CONCISE daily routine based on diagnosed conditions.

CRITICAL: Keep response SHORT and PRACTICAL. Max 3-5 bullet points per array. No lengthy paragraphs.

FIELD GUIDELINES:
- condition_summary: 1 sentence explaining the patient's situation
- daily_routine: Specific actionable steps for each time period (3-5 items each)
- diet_recommendations: Specific foods to eat (3-5 items)
- foods_to_limit: Specific foods to reduce/avoid (3-5 items)
- exercise_recommendations: Specific activities with frequency/duration (3-5 items)
- sleep_recommendations: Sleep hygiene practices (2-4 items)
- monitoring: What patient should track at home (3-5 items)
- avoid: Specific dangerous activities/habits (3-5 items)
- red_flags: Emergency symptoms requiring immediate medical attention (3-5 items)

Rules: No diagnosis, no medications, only lifestyle recommendations. Assume patient continues physician treatment.

Return STRICT JSON only with these exact fields."""

@app.post("/routine/from-disease")
def routine_from_disease(req: DiseaseRequest):
    prompt = f"Generate concise lifestyle routine for: {req.disease}"
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=SYSTEM_PROMPT,
        input=prompt,
        tools=[{"type": "web_search"}]
    )
    try:
        return json.loads(response.output_text)
    except:
        return {"raw_response": response.output_text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)