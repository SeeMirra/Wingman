#Portions copyright langchain, ray project, and their respective holders. All other portions copyright 2024 Christian Mirra
from typing import List

from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer


class LocalHuggingFaceEmbeddings(Embeddings):
    def __init__(self, model_id):
        self.model = SentenceTransformer(model_id)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using a locally running
           Hugging Face Sentence Transformer model

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        embeddings = self.model.encode(texts)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a query using a locally running HF
        Sentence transformer.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        embedding = self.model.encode(text)
        return list(map(float, embedding))
