import os
import hashlib
import json
from backend.services.ingestion import processing_status
from backend.services.ingestion.text_extractor import extract_text_from_pdf
from backend.services.ingestion.chunker import chunk_pages, save_chunks_to_jsonl
from backend.services.ingestion.document_indexer import DocumentMetadataStore
from backend.services.vector_store import VectorStore

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PDF_DIR = os.path.join(ROOT_DIR, "data", "pdfs")
INDEX_DIR = os.path.join(ROOT_DIR, "data", "extracted_text")


def calculate_file_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file on disk."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


class DocumentIngestionPipeline:
    """
    Generic Document Ingestion Pipeline:
    PDF -> SHA-256 -> Duplicate Check -> Inspection -> Text Layer Check -> Text Extraction
    -> Normalization -> Chunking -> Embeddings -> FAISS Index -> BM25 Index -> READY
    """

    @classmethod
    def find_existing_document(cls, sha256_hash: str) -> dict | None:
        """Search existing metadata records by SHA-256 hash."""
        if os.path.exists(INDEX_DIR):
            for fname in os.listdir(INDEX_DIR):
                if fname.endswith(".json"):
                    idx_path = os.path.join(INDEX_DIR, fname)
                    try:
                        with open(idx_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("sha256") == sha256_hash:
                            pdf_path = data.get("pdf_path")
                            if pdf_path and os.path.exists(pdf_path):
                                return data
                    except Exception:
                        continue
        return None

    @classmethod
    def process_pdf(cls, pdf_path: str, original_filename: str, stored_filename: str = None, document_type: str = "GENERAL_PDF") -> dict:
        """
        Execute end-to-end ingestion pipeline on a PDF file.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        doc_type = document_type.upper() if document_type else "GENERAL_PDF"
        if doc_type not in ["NOTES", "RESUME", "GENERAL_PDF"]:
            doc_type = "GENERAL_PDF"

        file_size = os.path.getsize(pdf_path)
        sha256_hash = calculate_file_sha256(pdf_path)
        document_id = sha256_hash[:8]

        if not stored_filename:
            stored_filename = os.path.basename(pdf_path)

        # 1. Duplicate Check
        existing = cls.find_existing_document(sha256_hash)
        if existing:
            existing_doc_id = existing.get("document_id", document_id)
            if doc_type == "RESUME":
                existing["document_type"] = "RESUME"
                if not existing.get("resume_data"):
                    try:
                        from backend.services.resume.resume_parser import parse_and_store_resume
                        parse_and_store_resume(existing_doc_id)
                    except Exception as parse_err:
                        print(f"Resume parsing warning for duplicate '{existing_doc_id}': {parse_err}")
                DocumentMetadataStore.save_metadata(existing)

            status = existing.get("processing_status", processing_status.READY)
            return {
                "success": True,
                "document_id": existing_doc_id,
                "document_type": existing.get("document_type", doc_type),
                "original_filename": original_filename,
                "stored_filename": existing.get("stored_filename", stored_filename),
                "sha256": sha256_hash,
                "file_size": existing.get("file_size", file_size),
                "page_count": existing.get("page_count", 0),
                "chunk_count": existing.get("chunk_count", 0),
                "processing_status": status,
                "has_text_layer": existing.get("has_text_layer", True),
                "message": "Document already exists and is registered."
            }

        # Initial Document Record (DISCOVERED)
        metadata = {
            "document_id": document_id,
            "document_type": doc_type,
            "filename": original_filename,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "pdf_path": pdf_path,
            "sha256": sha256_hash,
            "file_size": file_size,
            "page_count": 0,
            "pages_with_text": 0,
            "pages_with_images": 0,
            "has_text_layer": True,
            "chunk_count": 0,
            "embedding_count": 0,
            "total_words": 0,
            "processing_status": processing_status.DISCOVERED,
            "processing_error": None
        }
        DocumentMetadataStore.save_metadata(metadata)

        try:
            # 2. PDF Inspection & Text Extraction
            DocumentMetadataStore.update_status(document_id, processing_status.INSPECTING)
            DocumentMetadataStore.update_status(document_id, processing_status.EXTRACTING_TEXT)

            pages_data, summary = extract_text_from_pdf(pdf_path, document_id)

            metadata["page_count"] = summary["page_count"]
            metadata["pages_with_text"] = summary["pages_with_text"]
            metadata["pages_with_images"] = summary["pages_with_images"]
            metadata["has_text_layer"] = summary["has_text_layer"]
            metadata["total_words"] = summary["total_words"]
            metadata["pages"] = pages_data
            DocumentMetadataStore.save_metadata(metadata)

            # 3. Check for usable text layer (Image-Only / Scanned PDF)
            if not summary["has_text_layer"]:
                DocumentMetadataStore.update_status(
                    document_id,
                    processing_status.OCR_REQUIRED,
                    error_msg="No usable text layer found in PDF."
                )
                return {
                    "success": True,
                    "document_id": document_id,
                    "document_type": doc_type,
                    "original_filename": original_filename,
                    "stored_filename": stored_filename,
                    "sha256": sha256_hash,
                    "file_size": file_size,
                    "page_count": summary["page_count"],
                    "chunk_count": 0,
                    "processing_status": processing_status.OCR_REQUIRED,
                    "has_text_layer": False,
                    "message": "This PDF does not contain a usable text layer and requires OCR before it can be indexed."
                }

            # 4. Chunking
            DocumentMetadataStore.update_status(document_id, processing_status.CHUNKING)
            chunks = chunk_pages(document_id, pages_data)
            save_chunks_to_jsonl(document_id, chunks)

            metadata["chunk_count"] = len(chunks)
            DocumentMetadataStore.save_metadata(metadata)

            # 5. Embeddings & Indexing (FAISS & BM25)
            DocumentMetadataStore.update_status(document_id, processing_status.EMBEDDING)
            vs = VectorStore(document_id=document_id)
            vs.load_or_build_index()

            DocumentMetadataStore.update_status(document_id, processing_status.INDEXING)

            # 6. Mark READY
            metadata["embedding_count"] = len(chunks)
            metadata["processing_status"] = processing_status.READY
            DocumentMetadataStore.save_metadata(metadata)

            # If RESUME document_type, extract structured resume metadata
            if doc_type == "RESUME":
                try:
                    from backend.services.resume.resume_parser import parse_and_store_resume
                    parse_and_store_resume(document_id)
                except Exception as parse_err:
                    print(f"Resume parsing warning for '{document_id}': {parse_err}")

            return {
                "success": True,
                "document_id": document_id,
                "document_type": doc_type,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "sha256": sha256_hash,
                "file_size": file_size,
                "page_count": summary["page_count"],
                "chunk_count": len(chunks),
                "processing_status": processing_status.READY,
                "has_text_layer": True,
                "message": f"PDF processed successfully as {doc_type}. {len(chunks)} chunks indexed and ready."
            }

        except Exception as e:
            err_msg = str(e)
            DocumentMetadataStore.update_status(document_id, processing_status.FAILED, error_msg=err_msg)
            return {
                "success": False,
                "document_id": document_id,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "sha256": sha256_hash,
                "file_size": file_size,
                "page_count": metadata.get("page_count", 0),
                "chunk_count": 0,
                "processing_status": processing_status.FAILED,
                "has_text_layer": metadata.get("has_text_layer", True),
                "error": err_msg,
                "message": f"Failed to process PDF: {err_msg}"
            }
