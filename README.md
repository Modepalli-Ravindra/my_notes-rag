# MyNotes RAG

MyNotes RAG is a comprehensive Retrieval-Augmented Generation (RAG) application that provides intelligent interactions with your notes, documents, and resumes. It comes with powerful AI capabilities tailored for learning, recruitment, and coding evaluation.

## 🚀 Features

- **Document Ingestion & Analysis**: Upload and process notes, PDFs, and text documents.
- **Resume Analyzer**: Extract information from resumes, evaluate candidates, and generate personalized interview questions.
- **Viva & Interview Preparation**: AI-driven mock interviews and viva sessions.
- **Coding Evaluation**: Built-in tools for assessing and executing code snippets.
- **Multi-LLM Support**: Configured to work with various LLM providers (Gemini, Groq, NVIDIA, OpenRouter).

## 📁 Project Structure

- `backend/` - Python-based backend services containing ingestion pipelines, vector store management, and LLM integrations.
- `frontend/` - Next.js frontend application featuring a modern UI for uploading documents, conducting interviews, and managing resumes.
- `data/` - Datasets, extracted text, chunked data, and PDF storage.
- `models/` - Configuration and storage for AI/ML models and embeddings.
- `scratch/` - Testing scripts, evaluation scripts, and experimental features.

## 🛠️ Getting Started

### Prerequisites
- Node.js & npm (for the frontend)
- Python 3.8+ (for the backend)

### Installation & Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
# Add your API keys to .env
python main.py
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## 📄 License
This project is proprietary and confidential.
