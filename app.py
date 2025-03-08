from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import tempfile
from PIL import Image
import pytesseract
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX
import csv
import io
from pydantic import BaseModel
from typing import List, Optional
import re
from collections import Counter

app = FastAPI(title="Document Parser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParseResponse(BaseModel):
    success: bool
    text: str = ""
    error: str = ""
    file_type: str = ""
    suggested_tags: List[str] = []
    keywords: List[str] = []
    phrases: List[str] = []

def detect_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.docx':
        return 'docx'
    elif ext == '.txt':
        return 'txt'
    elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
        return 'image'
    elif ext == '.csv':
        return 'csv'
    else:
        return 'unknown'

def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF extraction error: {str(e)}")

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"DOCX extraction error: {str(e)}")

def extract_text_from_image(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        raise HTTPException(status_code=500, detail=f"Image OCR error: {str(e)}")

def extract_text_from_csv(file_path):
    try:
        text = ""
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                text += " ".join(row) + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from CSV: {e}")
        raise HTTPException(status_code=500, detail=f"CSV extraction error: {str(e)}")

def extract_text_from_file(file_path):
    file_type = detect_file_type(file_path)
    
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path), file_type
    elif file_type == 'docx':
        return extract_text_from_docx(file_path), file_type
    elif file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read(), file_type
    elif file_type == 'image':
        return extract_text_from_image(file_path), file_type
    elif file_type == 'csv':
        return extract_text_from_csv(file_path), file_type
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")

def extract_potential_tags(text):
    import re
    from collections import Counter
    
    # Extract capitalized phrases (potential named entities)
    capitalized_pattern = r'\b[A-Z][a-z]+ (?:[A-Z][a-z]+ )*[A-Z][a-z]+\b'
    capitalized_phrases = re.findall(capitalized_pattern, text)
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    stopwords = {'this', 'that', 'with', 'from', 'have', 'were', 'what', 'when', 'where', 
                'which', 'their', 'there', 'about', 'would', 'could', 'should'}
    filtered_words = [word for word in words if word not in stopwords]
    
    word_counts = Counter(filtered_words)
    common_words = [word for word, count in word_counts.most_common(5) if count > 1]
    
    all_tags = list(set(capitalized_phrases[:3] + common_words))
    
    return [tag[:20] + '...' if len(tag) > 20 else tag for tag in all_tags[:5]]

def extract_keywords(text, max_keywords=20):
    # Clean text
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    
    words = text.split()
    
    stopwords = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 
                'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 
                'between', 'both', 'but', 'by', 'could', 'did', 'do', 'does', 'doing', 'down', 
                'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 
                'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 
                'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'me', 'more', 'most', 'my', 
                'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 
                'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 
                'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 
                'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 
                'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 
                'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves'}
    
    filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
    
    word_counts = Counter(filtered_words)
    
    return [word for word, count in word_counts.most_common(max_keywords) if count > 1]

def extract_phrases(text, max_phrases=10):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    
    words = text.split()
    
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                'be', 'been', 'being', 'to', 'of', 'in', 'for', 'with', 'by', 'at', 
                'this', 'that', 'these', 'those', 'it', 'its'}
    
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    
    phrases = []
    
    for i in range(len(filtered_words) - 1):
        phrases.append(f"{filtered_words[i]} {filtered_words[i + 1]}")
    
    for i in range(len(filtered_words) - 2):
        phrases.append(f"{filtered_words[i]} {filtered_words[i + 1]} {filtered_words[i + 2]}")
    
    phrase_counts = Counter(phrases)
    
    # Get most common phrases
    return [phrase for phrase, count in phrase_counts.most_common(max_phrases) if count > 1]

@app.post("/parse", response_model=ParseResponse)
async def parse_document(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp:
        content = await file.read()
        temp.write(content)
        temp_path = temp.name
    
    try:
        text, file_type = extract_text_from_file(temp_path)
        
        suggested_tags = extract_potential_tags(text)
        
        keywords = extract_keywords(text)
        phrases = extract_phrases(text)
        
        return ParseResponse(
            success=True,
            text=text,
            file_type=file_type,
            suggested_tags=suggested_tags,
            keywords=keywords,
            phrases=phrases
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/health")
async def health_check():
    return "Yeah, server is running fine."

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)