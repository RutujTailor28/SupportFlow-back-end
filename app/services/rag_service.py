"""RAG service.

Future responsibilities:
- Knowledge base search
- Document chunking
- Embeddings
- Vector similarity search
- AI reply generation
- Content gap detection

Do not implement RAG yet.
"""


class RAGService:
    """Service layer for retrieval-augmented generation and KB search."""

    async def search_knowledge_base(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Search the knowledge base for relevant articles. Not implemented yet."""
        raise NotImplementedError("Knowledge base search will be implemented later.")

    async def chunk_documents(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Split documents into chunks for embedding. Not implemented yet."""
        raise NotImplementedError("Document chunking will be implemented later.")

    async def generate_embeddings(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Generate embeddings for document chunks. Not implemented yet."""
        raise NotImplementedError("Embedding generation will be implemented later.")

    async def vector_similarity_search(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Run vector similarity search. Not implemented yet."""
        raise NotImplementedError("Vector similarity search will be implemented later.")

    async def generate_reply(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Generate an AI-assisted support reply. Not implemented yet."""
        raise NotImplementedError("AI reply generation will be implemented later.")

    async def detect_content_gaps(self, *args, **kwargs):  # noqa: ANN002, ANN003
        """Detect knowledge base content gaps. Not implemented yet."""
        raise NotImplementedError("Content gap detection will be implemented later.")
