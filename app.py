from fastapi import FastAPI
from pydantic import BaseModel
import requests
import PyPDF2
import re

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

@app.post("/extract-topics")
async def extract_topics(data: ExtractRequest):
    pdf_url = data.url
    resp = requests.get(pdf_url)
    resp.raise_for_status()
    with open("temp.pdf", "wb") as f:
        f.write(resp.content)
    with open("temp.pdf", "rb") as f_pdf:
        reader = PyPDF2.PdfReader(f_pdf)
        text = ""
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                text += txt + "\n"
    # Match UNIT/CHAPTER/MODULE headings with optional Roman num/number/topic title
    # Example lines:
    # UNIT I INTRODUCTION TO OS
    # CHAPTER 2: FILE SYSTEMS
    # MODULE 3 – MEMORY MANAGEMENT
    topic_regex = re.compile(
        r'^(?:UNIT|MODULE|CHAPTER)[\s\-:\.]*([IVX0-9]+)?[\s:–\-\.]+([A-Z].+?)(?=\n|$)', re.MULTILINE|re.IGNORECASE
    )
    topics = [
        m.group(2).strip()
        for m in topic_regex.finditer(text)
        if m.group(2) and not re.search(r'author|reference|college', m.group(2), re.IGNORECASE)
    ]
    # As a failsafe, filter out lines that are just Roman numerals or nothing meaningful
    topics = [t for t in topics if len(t.split()) > 1 or t.isupper()]
    return {"topics": topics}
