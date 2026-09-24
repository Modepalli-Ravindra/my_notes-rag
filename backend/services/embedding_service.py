import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_EMBEDDING_MODEL_CACHE = {}


class EmbeddingService:
    """
    Local embedding service using HuggingFace Transformers and PyTorch.
    Computes mean-pooled L2-normalized embeddings for sentence-transformers/all-MiniLM-L6-v2.
    Remains 100% local, CPU-based, and free.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        cache_key = (self.model_name, self.device)
        if cache_key in _EMBEDDING_MODEL_CACHE:
            cached = _EMBEDDING_MODEL_CACHE[cache_key]
            self._use_st = cached["use_st"]
            if self._use_st:
                self._st_model = cached["model"]
            else:
                self._tokenizer = cached["tokenizer"]
                self._model = cached["model"]
            return

        if self._model is None or self._tokenizer is None:
            print(f"Loading embedding model '{self.model_name}' on {self.device}...")
            # Attempt loading via SentenceTransformer if available, fallback to AutoModel
            try:
                from sentence_transformers import SentenceTransformer
                st_model = SentenceTransformer(self.model_name, device=self.device)
                self._st_model = st_model
                self._use_st = True
                _EMBEDDING_MODEL_CACHE[cache_key] = {"use_st": True, "model": st_model}
                print(f"SentenceTransformer loaded successfully.")
                return
            except Exception as e:
                print(f"SentenceTransformer import failed ({str(e)}). Using HuggingFace Transformers fallback...")
                self._use_st = False
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModel.from_pretrained(self.model_name)
                self._model.to(self.device)
                self._model.eval()
                _EMBEDDING_MODEL_CACHE[cache_key] = {"use_st": False, "tokenizer": self._tokenizer, "model": self._model}
                print(f"HuggingFace AutoModel loaded successfully.")
        return

    def get_dimension(self) -> int:
        self._load_model()
        if hasattr(self, "_use_st") and self._use_st:
            return self._st_model.get_sentence_embedding_dimension()
        return self._model.config.hidden_size

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    def encode_texts(self, texts: list[str], batch_size: int = 32) -> tuple[np.ndarray, int]:
        """
        Batch encode a list of text strings into L2-normalized numpy embeddings.
        Returns tuple of (embeddings_ndarray, embedding_dimension).
        """
        if not texts:
            dim = self.get_dimension()
            return np.empty((0, dim), dtype=np.float32), dim

        self._load_model()

        if hasattr(self, "_use_st") and self._use_st:
            embeddings = self._st_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            embeddings_f32 = np.ascontiguousarray(embeddings.astype(np.float32))
            return embeddings_f32, embeddings_f32.shape[1]

        # Transformers fallback execution
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            encoded_input = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                model_output = self._model(**encoded_input)
                sentence_embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"])
                sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

            all_embeddings.append(sentence_embeddings.cpu().numpy())

        embeddings_f32 = np.ascontiguousarray(np.vstack(all_embeddings).astype(np.float32))
        return embeddings_f32, embeddings_f32.shape[1]

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single search query into an L2-normalized numpy array of shape (1, dimension).
        """
        embeddings, _ = self.encode_texts([query], batch_size=1)
        return embeddings
