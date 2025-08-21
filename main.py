from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
from openai import OpenAI

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

        # Limit text length to avoid exceeding token limit
        text = text[:2000]

        # 2. Ask OpenAI to generate flashcards
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a flashcard generator. Format output as JSON with 'question' and 'answer'."},
                {"role": "user", "content": f"Make 5 flashcards from this text:\n{text}"}
            ]
        )

        flashcards = response.choices[0].message.content

        return {"flashcards": flashcards}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
