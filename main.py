from fastapi import FastAPI, UploadFile, File
import pdfplumber
from openai import OpenAI

app = FastAPI()
client = OpenAI()  # uses OPENAI_API_KEY from environment

def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file.file) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

@app.get("/")
async def root():
    return {"message": "Flashcards backend is running 🚀"}

@app.post("/generate_flashcards")
async def generate_flashcards(pdf: UploadFile = File(...)):
    text = extract_text(pdf)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Make flashcards from this text:\n{text}"}]
    )

    return {"flashcards": response.choices[0].message["content"]}
