import math
import re
from pathlib import Path
from collections import Counter


class BM25Retriever:
    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)

        self.documents = []
        self.document_tokens = []
        self.document_frequencies = Counter()

        self.avg_document_length = 0.0

        self.k1 = 1.5
        self.b = 0.75

        self._load_documents()
        self._build_index()

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    def _load_documents(self):
        for path in sorted(self.knowledge_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8")

            self.documents.append(
                {
                    "name": path.name,
                    "text": text,
                }
            )

            self.document_tokens.append(
                self._tokenize(text)
            )

    def _build_index(self):
        if not self.documents:
            return

        for tokens in self.document_tokens:
            for token in set(tokens):
                self.document_frequencies[token] += 1

        total_length = sum(
            len(tokens)
            for tokens in self.document_tokens
        )

        self.avg_document_length = (
            total_length / len(self.document_tokens)
        )

    def _idf(self, term: str) -> float:
        document_count = len(self.documents)
        frequency = self.document_frequencies.get(term, 0)

        if frequency == 0:
            return 0.0

        return math.log(
            1 + (
                (document_count - frequency + 0.5)
                / (frequency + 0.5)
            )
        )

    def _score(self, query_tokens: list[str], index: int) -> float:
        tokens = self.document_tokens[index]
        term_frequencies = Counter(tokens)

        document_length = len(tokens)

        score = 0.0

        for term in query_tokens:
            frequency = term_frequencies.get(term, 0)

            if frequency == 0:
                continue

            idf = self._idf(term)

            numerator = (
                frequency * (self.k1 + 1)
            )

            denominator = (
                frequency
                + self.k1
                * (
                    1
                    - self.b
                    + self.b
                    * (
                        document_length
                        / self.avg_document_length
                    )
                )
            )

            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 3):
        query_tokens = self._tokenize(query)

        scored_documents = []

        for index, document in enumerate(self.documents):
            score = self._score(
                query_tokens,
                index,
            )

            scored_documents.append(
                {
                    "document": document["name"],
                    "score": score,
                }
            )

        scored_documents.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored_documents[:top_k]

    @property
    def document_count(self) -> int:
        return len(self.documents)