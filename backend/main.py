import os
import re
import uuid
import json
import hashlib
import pymupdf
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="MyNotes RAG Backend")

# CORS setup for Next.js frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Target directory for uploaded PDFs and extracted metadata
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
INDEX_DIR = os.path.join(BASE_DIR, "data", "extracted_text")
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)

# Load environment variables from backend/.env safely
try:
    import dotenv
    env_file = os.path.join(BASE_DIR, "backend", ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
except Exception:
    pass

_VECTOR_STORES = {}

def get_vector_store(document_id: str = "b8f2cb48"):
    """Reuse cached VectorStore instance to prevent reloading embeddings on every request."""
    if document_id not in _VECTOR_STORES:
        from backend.services.vector_store import VectorStore
        vs = VectorStore(document_id=document_id)
        vs.load_or_build_index()
        _VECTOR_STORES[document_id] = vs
    return _VECTOR_STORES[document_id]


MAX_FILE_SIZE = 150 * 1024 * 1024  # 150 MB limit
CHUNK_SIZE = 1024 * 1024  # 1 MB streaming chunks for memory efficiency


def calculate_file_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file on disk."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell execution vulnerabilities."""
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', clean_name)
    if not clean_name or clean_name == ".pdf":
        clean_name = f"document_{uuid.uuid4().hex[:6]}.pdf"
    return clean_name


def inspect_and_extract_pdf(pdf_path: str, document_id: str, stored_filename: str, original_filename: str, sha256_hash: str = None):
    """
    Inspect PDF using PyMuPDF (pymupdf), count pages, verify text and image layers,
    compute SHA-256 hash, and preserve extracted text layer for future RAG processing.
    """
    if not sha256_hash:
        sha256_hash = calculate_file_sha256(pdf_path)

    file_size = os.path.getsize(pdf_path)

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted PDF file: {str(e)}"
        )

    page_count = len(doc)
    pages_with_text = 0
    pages_with_images = 0
    extracted_pages = []

    for i in range(page_count):
        page = doc[i]
        text = page.get_text() or ""
        has_text = bool(text.strip())
        images = page.get_images()
        has_image = bool(images and len(images) > 0)

        if has_text:
            pages_with_text += 1
        if has_image:
            pages_with_images += 1

        extracted_pages.append({
            "page_num": i + 1,
            "text": text,
            "has_text": has_text,
            "has_image": has_image
        })

    doc.close()

    has_text_layer = (pages_with_text > 0)

    # Store extracted page-level text in document index file for future RAG retrieval
    doc_index = {
        "document_id": document_id,
        "sha256": sha256_hash,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "pdf_path": pdf_path,
        "file_size": file_size,
        "page_count": page_count,
        "has_text_layer": has_text_layer,
        "pages_with_text": pages_with_text,
        "pages_with_images": pages_with_images,
        "pages": extracted_pages
    }

    index_path = os.path.join(INDEX_DIR, f"{document_id}.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(doc_index, f, ensure_ascii=False, indent=2)

    return doc_index


def find_existing_document_by_sha256(sha256_hash: str) -> dict | None:
    """
    Search indexed documents for matching SHA-256 hash.
    Also registers unindexed PDFs present in data/pdfs.
    """
    # 1. Search index files in INDEX_DIR
    if os.path.exists(INDEX_DIR):
        for fname in os.listdir(INDEX_DIR):
            if fname.endswith(".json"):
                idx_path = os.path.join(INDEX_DIR, fname)
                try:
                    with open(idx_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("sha256") == sha256_hash:
                        # Verify PDF file still exists on disk
                        pdf_path = data.get("pdf_path")
                        if pdf_path and os.path.exists(pdf_path):
                            return data
                except Exception:
                    continue

    # 2. Check PDFs in PDF_DIR for unindexed files matching SHA-256
    if os.path.exists(PDF_DIR):
        for fname in os.listdir(PDF_DIR):
            if fname.lower().endswith(".pdf"):
                pdf_path = os.path.join(PDF_DIR, fname)
                if os.path.isfile(pdf_path):
                    h_val = calculate_file_sha256(pdf_path)
                    if h_val == sha256_hash:
                        doc_id = h_val[:8]
                        idx_path = os.path.join(INDEX_DIR, f"{doc_id}.json")
                        if not os.path.exists(idx_path):
                            # Auto-index manually placed PDF
                            doc_data = inspect_and_extract_pdf(pdf_path, doc_id, fname, fname, sha256_hash=h_val)
                            return doc_data
                        else:
                            try:
                                with open(idx_path, "r", encoding="utf-8") as f:
                                    return json.load(f)
                            except Exception:
                                pass
    return None


from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Semantic search query string")
    top_k: int = Field(5, ge=1, le=10, description="Number of top relevant chunks to retrieve (1-10)")
    document_id: str | None = Field(None, description="Target document ID (optional; if omitted, searches all READY documents)")


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question string")
    top_k: int = Field(5, ge=1, le=10, description="Top K retrieval count (1-10)")
    provider: str | None = Field(None, description="Target LLM provider ('groq', 'openrouter', 'nvidia', 'gemini')")
    document_id: str | None = Field(None, description="Target document ID (optional; if omitted, searches all READY documents)")


@app.get("/")
def root():
    return {"message": "MyNotes RAG Backend Running"}


@app.post("/search")
def search_documents(request: SearchRequest):
    """
    Perform semantic vector search + BM25 lexical search across all READY documents or a specific document.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    try:
        from backend.services.vector_store import search_multi_documents
        results = search_multi_documents(query=request.query.strip(), top_k=request.top_k, document_id=request.document_id)

        return {
            "query": request.query.strip(),
            "document_id": request.document_id,
            "top_k": request.top_k,
            "count": len(results),
            "results": results
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )


@app.post("/ask")
def ask_question(request: AskRequest):
    """
    Grounded RAG endpoint:
    1. Performs multi-document hybrid FAISS + BM25 retrieval.
    2. Builds grounded context prompt with source citations.
    3. Calls configured LLM provider (or fallback chain) to generate answer.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        from backend.services.vector_store import search_multi_documents
        retrieved_chunks = search_multi_documents(query=request.query.strip(), top_k=request.top_k, document_id=request.document_id)

        from backend.services.llm.provider_manager import LLMProviderManager
        from backend.services.llm.base_provider import LLMProviderError

        manager = LLMProviderManager()
        response_data, trace_data = manager.generate_grounded_answer(
            query=request.query.strip(),
            retrieved_chunks=retrieved_chunks,
            requested_provider=request.provider,
            max_context_chunks=request.top_k
        )

        response_data["trace"] = trace_data

        # Generate dedicated Gemini Mana-Style Explanation
        try:
            from backend.services.mana_explanation import ManaExplanationService
            context_text = "\n".join([c.get("text", "") for c in retrieved_chunks])
            mana_exp = ManaExplanationService.generate_mana_explanation(
                question=request.query.strip(),
                technical_answer=response_data.get("answer", ""),
                source_context=context_text,
                mode="NORMAL_RAG"
            )
            if mana_exp:
                response_data["mana_explanation"] = mana_exp
        except Exception as me_err:
            print(f"Mana explanation integration note: {me_err}")

        return response_data

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        from backend.services.llm.base_provider import LLMProviderError
        if isinstance(e, LLMProviderError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM Generation Failed: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG process failed: {str(e)}"
        )




@app.get("/documents")
def list_documents():
    """Retrieve all registered documents metadata via DocumentMetadataStore."""
    from backend.services.ingestion.document_indexer import DocumentMetadataStore
    docs = DocumentMetadataStore.list_all_documents()
    return {"documents": docs, "count": len(docs)}


@app.get("/documents/{document_id}")
def get_document(document_id: str):
    """Retrieve full metadata for a specific document by document_id."""
    idx_path = os.path.join(INDEX_DIR, f"{document_id}.json")
    if not os.path.exists(idx_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found."
        )
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading document metadata: {str(e)}"
        )


@app.get("/documents/{document_id}/pages")
def get_document_pages(document_id: str, page: int = 1, limit: int = 20):
    """Retrieve paginated page-level text metadata for a document."""
    idx_path = os.path.join(INDEX_DIR, f"{document_id}.json")
    if not os.path.exists(idx_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found."
        )

    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pages = data.get("pages", [])
        total_pages = len(pages)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_pages = pages[start_idx:end_idx]

        return {
            "document_id": document_id,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "count": len(paginated_pages),
            "pages": paginated_pages
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading document pages: {str(e)}"
        )


@app.get("/documents/{document_id}/pages/{page_number}/image")
def get_document_page_image(document_id: str, page_number: int, dpi: int = 150):
    """
    Render and stream a single page of a document as a PNG image using PyMuPDF.
    On-demand rendering in memory: no permanent image files are created on disk.
    """
    idx_path = os.path.join(INDEX_DIR, f"{document_id}.json")
    if not os.path.exists(idx_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found."
        )

    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        pdf_path = meta.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            stored_name = meta.get("stored_filename") or meta.get("original_filename")
            if stored_name and os.path.exists(os.path.join(PDF_DIR, stored_name)):
                pdf_path = os.path.join(PDF_DIR, stored_name)
            elif os.path.exists(os.path.join(PDF_DIR, "my-notes.pdf")):
                pdf_path = os.path.join(PDF_DIR, "my-notes.pdf")
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PDF source file for document '{document_id}' is missing."
                )

        page_count = meta.get("page_count", 0)
        if page_number < 1 or page_number > page_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page number {page_number} is out of bounds. Document has {page_count} pages."
            )

        # Open PDF and render requested page in memory using PyMuPDF
        doc = pymupdf.open(pdf_path)
        page = doc[page_number - 1]  # PyMuPDF is 0-indexed
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        doc.close()

        return Response(
            content=img_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Document-ID": document_id,
                "X-Page-Number": str(page_number),
                "X-Total-Pages": str(page_count)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render page image."
        )


@app.get("/documents/{document_id}/chunks")

def get_document_chunks(document_id: str, page: int = 1, limit: int = 20):
    """Retrieve paginated chunk metadata from JSONL file for a document."""
    jsonl_path = os.path.join(CHUNKS_DIR, f"{document_id}.jsonl")
    if not os.path.exists(jsonl_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunks for document '{document_id}' not found."
        )

    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    try:
        chunks = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))

        total_chunks = len(chunks)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_chunks = chunks[start_idx:end_idx]

        return {
            "document_id": document_id,
            "page": page,
            "limit": limit,
            "total_chunks": total_chunks,
            "count": len(paginated_chunks),
            "chunks": paginated_chunks
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading document chunks: {str(e)}"
        )



@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), document_type: str = Form("GENERAL_PDF")):
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided."
        )

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files (.pdf) are allowed."
        )

    if file.content_type and file.content_type.lower() not in ["application/pdf", "application/x-pdf"]:
        if not file.content_type.lower().startswith("application/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MIME type. Upload must be a valid PDF document."
            )

    clean_orig_name = sanitize_filename(filename)
    temp_filename = f"temp_{uuid.uuid4().hex}.pdf"
    temp_path = os.path.join(PDF_DIR, temp_filename)

    hasher = hashlib.sha256()
    file_size = 0

    try:
        # Stream incoming upload to temp file while calculating SHA-256 in memory
        with open(temp_path, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    f.close()
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeds maximum limit of 150 MB (uploaded >150 MB)."
                    )
                hasher.update(chunk)
                f.write(chunk)

        if file_size == 0:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF file is empty."
            )

        sha256_hash = hasher.hexdigest()
        document_id = sha256_hash[:8]
        stored_filename = clean_orig_name
        target_path = os.path.join(PDF_DIR, stored_filename)

        if os.path.exists(target_path) and calculate_file_sha256(target_path) != sha256_hash:
            name_part, extension = os.path.splitext(clean_orig_name)
            stored_filename = f"{name_part}_{document_id}{extension}"
            target_path = os.path.join(PDF_DIR, stored_filename)

        if not os.path.exists(target_path):
            os.replace(temp_path, target_path)
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Run DocumentIngestionPipeline
        from backend.services.ingestion import DocumentIngestionPipeline
        pipeline_result = DocumentIngestionPipeline.process_pdf(target_path, filename, stored_filename, document_type=document_type)

        return JSONResponse(
            status_code=status.HTTP_200_OK if pipeline_result.get("success") else status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=pipeline_result
        )

    except HTTPException:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save PDF to server disk: {str(e)}"
        )


# ==================================================
# RESUME INTELLIGENCE & VIVA ENDPOINTS
# ==================================================

class ResumeQuestionsRequest(BaseModel):
    document_id: str
    mode: str = Field("technical", description="hr | technical | project | viva | mixed")
    role: str | None = Field(None, description="Target job role")
    difficulty: str = Field("medium", description="easy | medium | hard")
    count: int = Field(5, ge=1, le=20)


class VivaStartRequest(BaseModel):
    document_id: str | None = None
    mode: str = Field("general", description="general | resume | project | technical")
    difficulty: str = Field("medium", description="easy | medium | hard")
    count: int = Field(5, ge=1, le=20)


class VivaAnswerRequest(BaseModel):
    document_id: str | None = None
    question: str
    user_answer: str
    mode: str = Field("general")
    include_notes_rag: bool = False


class InterviewCoachingRequest(BaseModel):
    question: str
    document_id: str | None = None
    include_notes_rag: bool = True


@app.get("/resume/{document_id}/analysis")
def get_resume_analysis(document_id: str):
    """Retrieve structured resume metadata analysis and question triggers."""
    try:
        from backend.services.resume.resume_analyzer import ResumeAnalyzer
        analysis = ResumeAnalyzer.get_or_analyze_resume(document_id)
        return analysis
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Resume analysis failed: {str(e)}")


@app.post("/resume/questions")
def generate_resume_questions(request: ResumeQuestionsRequest):
    """Generate structured interview questions grounded in actual resume content."""
    try:
        from backend.services.resume.resume_question_generator import ResumeQuestionGenerator
        result = ResumeQuestionGenerator.generate_questions(
            document_id=request.document_id,
            mode=request.mode,
            role=request.role,
            difficulty=request.difficulty,
            count=request.count
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Question generation failed: {str(e)}")


@app.post("/resume/session/start")
def start_viva_session(request: VivaStartRequest):
    """Start an interactive Viva or Interview session."""
    try:
        from backend.services.resume.resume_question_generator import ResumeQuestionGenerator
        doc_id = request.document_id or "b8f2cb48"
        questions_resp = ResumeQuestionGenerator.generate_questions(
            document_id=doc_id,
            mode=request.mode,
            difficulty=request.difficulty,
            count=request.count
        )
        qs = questions_resp.get("questions", [])
        first_q = qs[0]["question"] if qs else "Can you introduce yourself and walk me through your key technical projects?"
        return {
            "session_id": f"viva_{uuid.uuid4().hex[:6]}",
            "document_id": request.document_id,
            "mode": request.mode,
            "difficulty": request.difficulty,
            "current_question": first_q,
            "total_questions": len(qs),
            "questions": qs
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start viva session: {str(e)}")


@app.post("/resume/session/answer")
def submit_viva_answer(request: VivaAnswerRequest):
    """Evaluate candidate viva answer, return feedback, Mana-style explanation, and follow-up question."""
    if not request.question or not request.user_answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question and user_answer are required.")

    notes_context = None
    if request.include_notes_rag:
        try:
            from backend.services.vector_store import search_multi_documents
            chunks = search_multi_documents(query=request.question, top_k=2)
            if chunks:
                notes_context = "\n".join([c.get("text", "") for c in chunks])
        except Exception:
            pass

    try:
        from backend.services.resume.resume_viva import VivaEngine
        evaluation = VivaEngine.evaluate_viva_answer(
            document_id=request.document_id,
            question=request.question,
            user_answer=request.user_answer,
            mode=request.mode,
            notes_context=notes_context
        )
        return evaluation
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Answer evaluation failed: {str(e)}")


@app.post("/resume/coaching")
def generate_interview_coaching(request: InterviewCoachingRequest):
    """Generate interview-ready answer coaching with Mana-style explanation."""
    if not request.question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required.")

    resume_context = None
    if request.document_id:
        try:
            from backend.services.resume.resume_analyzer import ResumeAnalyzer
            analysis = ResumeAnalyzer.get_or_analyze_resume(request.document_id)
            resume_context = json.dumps(analysis.get("resume_data", {}), ensure_ascii=False)
        except Exception:
            pass

    notes_context = None
    if request.include_notes_rag:
        try:
            from backend.services.vector_store import search_multi_documents
            chunks = search_multi_documents(query=request.question, top_k=2)
            if chunks:
                notes_context = "\n".join([c.get("text", "") for c in chunks])
        except Exception:
            pass

    try:
        from backend.services.resume.resume_feedback import InterviewCoachingEngine
        coaching = InterviewCoachingEngine.generate_coaching(
            question=request.question,
            resume_context=resume_context,
            notes_context=notes_context
        )
        return coaching
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Interview coaching failed: {str(e)}")


# ==================================================
# CODING INTERVIEW ENDPOINTS
# ==================================================

class CodingProblemRequest(BaseModel):
    language: str = Field("Python", description="Python | Java | JavaScript | SQL")
    difficulty: str = Field("medium", description="easy | medium | hard")
    topic: str = Field("arrays", description="Topic area")
    role: str | None = Field(None, description="Target role")
    document_id: str | None = Field(None, description="Optional resume document_id")
    include_notes_rag: bool = False


class CodingExecuteRequest(BaseModel):
    language: str
    code: str
    input_data: str = ""
    setup_sql: str | None = None


class CodingEvaluateRequest(BaseModel):
    language: str
    code: str
    problem_statement: str
    starter_code: str | None = None
    setup_sql: str | None = None


@app.post("/coding/problem/generate")
def generate_coding_problem(request: CodingProblemRequest):
    """Generate a structured coding problem customized for language, topic, difficulty, role, resume, or notes."""
    try:
        from backend.services.coding.code_evaluator import CodeEvaluator
        problem = CodeEvaluator.generate_problem(
            language=request.language,
            difficulty=request.difficulty,
            topic=request.topic,
            role=request.role,
            document_id=request.document_id,
            include_notes_rag=request.include_notes_rag
        )
        return problem
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Problem generation failed: {str(e)}")


@app.post("/coding/execute")
def execute_code(request: CodingExecuteRequest):
    """Run code securely via subprocess and return output/errors."""
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code parameter cannot be empty.")
    
    try:
        from backend.services.coding.code_executor import CodeExecutor
        result = CodeExecutor.execute(
            language=request.language,
            code=request.code,
            input_data=request.input_data,
            setup_sql=request.setup_sql
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Code execution error: {str(e)}")


@app.post("/coding/evaluate")
def evaluate_code(request: CodingEvaluateRequest):
    """Submit code for evaluation, feedback, complexity analysis, and Mana-style explanation."""
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code parameter cannot be empty.")

    try:
        from backend.services.coding.code_evaluator import CodeEvaluator
        result = CodeEvaluator.evaluate_submission(
            language=request.language,
            code=request.code,
            problem_statement=request.problem_statement,
            starter_code=request.starter_code,
            setup_sql=request.setup_sql
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Code evaluation error: {str(e)}")



