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
    request: Request,
    pdf: UploadFile = File(None),      # optional
    num_flashcards: int = Form(5),
    topic: str = Form(None),
    text: str = Form(None)             # 🔥 NEW: direct text input
):
    start_time = time.time()
    try:
        if text:
            # 🔥 Use text extracted by frontend
            extracted_text = text[:2000]
        elif pdf:
            # fallback: extract from PDF server-side
            extracted_text = ""
            with pdfplumber.open(pdf.file) as pdf_obj:
                for page in pdf_obj.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                    if len(extracted_text) > 2000:
                        break
            extracted_text = extracted_text[:2000]
        else:
            raise HTTPException(status_code=400, detail="No input provided")

        # --- Build prompt
        if topic:
            user_prompt = (
                f"Generate exactly {num_flashcards} flashcards only about the topic '{topic}' "
                f"from the following text. Ignore unrelated content.\n\n"
                f'{{"flashcards": [{{"question": "...", "answer": "..."}}]}}\n\n'
                f"Text:\n{extracted_text}"
            )
        else:
            user_prompt = (
                f"Generate exactly {num_flashcards} flashcards from the following text.\n\n"
                f'{{"flashcards": [{{"question": "...", "answer": "..."}}]}}\n\n'
                f"Text:\n{extracted_text}"
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
