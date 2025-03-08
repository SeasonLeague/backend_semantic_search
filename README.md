# Semantic Search Engine

A web application for semantic document search with support for various document formats.

## Features

- Upload and manage documents (TXT, PDF, DOC, DOCX, CSV, images)
- Extract text from various file formats
- Search documents with semantic relevance
- Highlight matching sections in search results
- Tag documents for better organization
- Search history and suggestions
- Document persistence

## Project Structure

- **Frontend**: Next.js application with React components
- **Document Parser API**: FastAPI service for document parsing and text extraction

## Setup Instructions

### 1. Set up the Document Parser API

```bash
cd document-parser-api
pip install -r requirements.txt

# Install Tesseract OCR (for image text extraction)
# On Ubuntu:
sudo apt-get install tesseract-ocr
# On macOS:
brew install tesseract
# On Windows:
# Download and install from https://github.com/UB-Mannheim/tesseract/wiki

# Start the API server
python main.py
