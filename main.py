from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
from openai import OpenAI
import json
import time

app = FastAPI()
client = OpenAI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Flashcards backend is running 🚀"}

@app.get("/health")
async def health():
    return {"alive": True}

@app.get("/status")
async def status():
    return {
        "status": "ok ✅",
        "endpoints": {
            "root": "/",
            "generate_flashcards": "/generate_flashcards",
            "status": "/status",
            "health": "/health"
        },
        "config": {
            "model": "gpt-4o-mini",
            "pdf_text_limit": 2000,
            "default_flashcards": 5
        }
    }

@app.post("/generate_flashcards")
async def generate_flashcards(
    request: Request,
    pdf: UploadFile = File(...),
    num_flashcards: int = Form(5),
    topic: str = Form(None)  # 🔥 new optional topic filter
):
    start_time = time.time()  # ⏱ start timing
    try:
        print(f"📂 Uploaded file: {pdf.filename}")
        print(f"📝 Flashcards requested: {num_flashcards}")
        if topic:
            print(f"🔎 Topic filter: {topic}")

        # --- Extract PDF text ---
        text = ""
        with pdfplumber.open(pdf.file) as pdf_obj:
            for page_num, page in enumerate(pdf_obj.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    print(f"   Extracted text from page {page_num} ({len(page_text)} chars)")
                    text += page_text + "\n"

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF")

        # limit to avoid too large payload
        text = text[:2000]

        # --- Build Prompt ---
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

        # --- OpenAI Request ---
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
            print("❌ JSON parse failed, returning dummy flashcards:", e)
            flashcards = [
                {"question": "Sample Question 1", "answer": "Sample Answer 1"},
                {"question": "Sample Question 2", "answer": "Sample Answer 2"},
            ]

        duration = round(time.time() - start_time, 2)  # ⏱ end timing
        print(f"✅ Request processed in {duration} seconds")

        return {
            "flashcards": flashcards,
            "processing_time": duration,
            "topic_used": topic if topic else None
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        duration = round(time.time() - start_time, 2)
        print(f"❌ Error after {duration} seconds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
