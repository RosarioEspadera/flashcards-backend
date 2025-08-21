from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
from openai import OpenAI
import json

app = FastAPI()
client = OpenAI()

# Enable CORS for frontend
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
    pdf: UploadFile = File(...),
    num_flashcards: int = Form(5)  # default = 5
):
    try:
        text = ""
        with pdfplumber.open(pdf.file) as pdf_obj:
            for page in pdf_obj.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF")

        # Limit text size (to avoid hitting token limits)
        text = text[:2000]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Make {num_flashcards} flashcards from this text as a valid JSON array with 'question' and 'answer' fields only. Do not include extra text or markdown:\n{text}"
                }
            ]
        )

        # FIX: new OpenAI SDK indexing
        raw_output = response.choices[0].message["content"].strip()

        # Parse JSON
        try:
            flashcards = json.loads(raw_output)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Model did not return valid JSON")

        return {"flashcards": flashcards}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
