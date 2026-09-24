import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase alphanumeric terms and words.
    Preserves technical terms, acronyms, and words.
    """
    if not text:
        return []
    # Extract words/tokens consisting of letters, digits, and underscores
    tokens = re.findall(r'[a-zA-Z0-9_]+', text.lower())
    return tokens


class BM25Retriever:
    """
    Lightweight, local Okapi BM25 implementation for lexical document scoring.
    Does not require external services or paid APIs.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.idf = {}
        self.is_built = False

    def build_index(self, corpus_texts: list[str]):
        """
        Build BM25 index from a list of document/chunk texts.
        """
        self.corpus_size = len(corpus_texts)
        if self.corpus_size == 0:
            self.is_built = True
            return

        self.doc_lengths = []
        self.doc_term_freqs = []
        total_length = 0
        df = Counter()

        for text in corpus_texts:
            tokens = tokenize(text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            for term in tf.keys():
                df[term] += 1

        self.avg_doc_len = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Calculate Okapi BM25 IDF for each term
        self.idf = {}
        for term, freq in df.items():
            # BM25 IDF formula with smoothing
            idf_val = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
            self.idf[term] = max(0.0, idf_val)

        self.is_built = True

    def get_scores(self, query: str) -> list[float]:
        """
        Calculate BM25 raw scores for a query against all indexed documents.
        """
        if not self.is_built or self.corpus_size == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return [0.0] * self.corpus_size

        scores = [0.0] * self.corpus_size

        for q_token in query_tokens:
            if q_token not in self.idf:
                continue
            idf_val = self.idf[q_token]

            for doc_idx, tf_map in enumerate(self.doc_term_freqs):
                if q_token not in tf_map:
                    continue
                tf = tf_map[q_token]
                doc_len = self.doc_lengths[doc_idx]

                # BM25 term score formula
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                term_score = idf_val * (numerator / denominator)
                scores[doc_idx] += term_score

        return scores
