from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
from openai import OpenAI
import json
import re

app = FastAPI()
client = OpenAI()

@app.get("/")
async def root():
    return {"message": "Flashcards backend is running 🚀"}

@app.post("/generate_flashcards")
async def generate_flashcards(pdf: UploadFile = File(...)):
    try:
        # 1. Extract text from uploaded PDF
        text = ""
        with pdfplumber.open(pdf.file) as pdf_obj:
            for page in pdf_obj.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF")

        # Cut text for testing
        text = text[:2000]

        # 2. Ask OpenAI for flashcards
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a flashcard generator. Always output only JSON array with 'question' and 'answer'."},
                {"role": "user", "content": f"Make 5 flashcards from this text:\n{text}"}
            ]
        )

        raw_output = response.choices[0].message.content

        # 3. Clean and parse JSON
        cleaned = re.sub(r"```json|```", "", raw_output).strip()

        try:
            flashcards = json.loads(cleaned)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")

        return {"flashcards": flashcards}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
