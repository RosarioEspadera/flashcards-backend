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
    text: str = Form(...),            # 🔥 now text is sent directly
    num_flashcards: int = Form(5),
    topic: str = Form(None)
):
    start_time = time.time()
    try:
        print(f"📝 Flashcards requested: {num_flashcards}")
        if topic:
            print(f"🔎 Topic filter: {topic}")
        print(f"📄 Received text length: {len(text)} chars")

        # Safety limit
        text = text[:2000]

        # Build Prompt
        if topic:
            user_prompt = (
                f"Generate exactly {num_flashcards} flashcards only about the topic '{topic}' "
                f"from the following text. Ignore unrelated content.\n\n"
                f'Return JSON in this structure:\n'
                f'{{"flashcards": [{{"question": "...", "answer": "..."}}]}}.\n\n'
                f"Text:\n{text}"
            )
        else:
            user_prompt = (
                f"Generate exactly {num_flashcards} flashcards from the following text.\n\n"
                f'Return JSON in this structure:\n'
                f'{{"flashcards": [{{"question": "...", "answer": "..."}}]}}.\n\n'
                f"Text:\n{text}"
            )

        # OpenAI call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a JSON generator. Always return valid JSON only."},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw_output = response.choices[0].message.content.strip()
        print("\n===== RAW MODEL OUTPUT =====")
        print(raw_output)
        print("============================\n")

        try:
            parsed = json.loads(raw_output)
            flashcards = parsed.get("flashcards", [])
        except Exception as e:
            print("❌ JSON parse failed:", e)
            flashcards = [{"question": "Sample Q", "answer": "Sample A"}]

        duration = round(time.time() - start_time, 2)
        return {"flashcards": flashcards, "processing_time": duration, "topic_used": topic or None}

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
