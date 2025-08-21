from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import json, time

app = FastAPI()
client = OpenAI()

# Enable CORS (adjust if you want specific frontend domain only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Flashcards backend is running 🚀"}

@app.post("/generate_flashcards")
async def generate_flashcards(
    text: str = Form(...),               # frontend sends extracted text here
    num_flashcards: int = Form(5),
    topic: str = Form(None)
):
    start_time = time.time()

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    # --- Build Prompt ---
    if topic:
        user_prompt = (
            f"Generate exactly {num_flashcards} flashcards only about '{topic}' "
            f"from the following text. Ignore unrelated content.\n\n"
            f'Return JSON in this structure:\n'
            f'{{"flashcards":[{{"question":"...","answer":"..."}}]}}\n\n'
            f"Text:\n{text}"
        )
    else:
        user_prompt = (
            f"Generate exactly {num_flashcards} flashcards from the following text.\n\n"
            f'Return JSON in this structure:\n'
            f'{{"flashcards":[{{"question":"...","answer":"..."}}]}}\n\n'
            f"Text:\n{text}"
        )

    # --- Call OpenAI ---
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a JSON generator. Always return valid JSON only."},
            {"role": "user", "content": user_prompt}
        ]
    )

    raw_output = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw_output)
        flashcards = parsed.get("flashcards", [])
    except Exception:
        flashcards = [{"question": "Fallback Q", "answer": "Fallback A"}]

    return {
        "flashcards": flashcards,
        "processing_time": round(time.time()-start_time,2),
        "topic_used": topic or None
    }
