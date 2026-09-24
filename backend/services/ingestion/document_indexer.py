import os
import json
import time
from backend.services.ingestion import processing_status

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
INDEX_DIR = os.path.join(ROOT_DIR, "data", "extracted_text")
os.makedirs(INDEX_DIR, exist_ok=True)


class DocumentMetadataStore:
    """Manages document metadata JSON records in data/extracted_text/<document_id>.json."""

    @staticmethod
    def get_metadata_path(document_id: str) -> str:
        return os.path.join(INDEX_DIR, f"{document_id}.json")

    @classmethod
    def load_metadata(cls, document_id: str) -> dict | None:
        idx_path = cls.get_metadata_path(document_id)
        if not os.path.exists(idx_path):
            return None
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @classmethod
    def save_metadata(cls, metadata: dict) -> str:
        document_id = metadata["document_id"]
        idx_path = cls.get_metadata_path(document_id)
        
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if "created_at" not in metadata:
            metadata["created_at"] = now_str
        metadata["updated_at"] = now_str

        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return idx_path

    @classmethod
    def update_status(cls, document_id: str, status: str, error_msg: str | None = None, extra_fields: dict | None = None) -> dict | None:
        meta = cls.load_metadata(document_id)
        if not meta:
            return None
        meta["processing_status"] = status
        meta["processing_error"] = error_msg
        if extra_fields:
            meta.update(extra_fields)
        cls.save_metadata(meta)
        return meta

    @classmethod
    def list_all_documents(cls) -> list[dict]:
        docs = []
        if os.path.exists(INDEX_DIR):
            for fname in os.listdir(INDEX_DIR):
                if fname.endswith(".json"):
                    idx_path = os.path.join(INDEX_DIR, fname)
                    try:
                        with open(idx_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        pdf_path = data.get("pdf_path", "")
                        rel_path = os.path.relpath(pdf_path, ROOT_DIR).replace("\\", "/") if pdf_path else ""
                        docs.append({
                            "document_id": data.get("document_id"),
                            "document_type": data.get("document_type", "NOTES" if data.get("document_id") == "b8f2cb48" else "GENERAL_PDF"),
                            "sha256": data.get("sha256"),
                            "original_filename": data.get("original_filename") or data.get("filename"),
                            "stored_filename": data.get("stored_filename"),
                            "file_size": data.get("file_size"),
                            "file_path": rel_path,
                            "page_count": data.get("page_count", 0),
                            "has_text_layer": data.get("has_text_layer", True),
                            "pages_with_text": data.get("pages_with_text", 0),
                            "pages_with_images": data.get("pages_with_images", 0),
                            "chunk_count": data.get("chunk_count", 0),
                            "embedding_count": data.get("embedding_count", data.get("chunk_count", 0)),
                            "total_words": data.get("total_words", 0),
                            "processing_status": data.get("processing_status", processing_status.READY),
                            "processing_error": data.get("processing_error"),
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at")
                        })
                    except Exception:
                        continue
        return docs
