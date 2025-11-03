"""
RAG Chunking Strategy for Ticket Data

Chunks tickets into semantic pieces for better retrieval and context fitting.
"""
from typing import List, Dict, Any
import re


class RAGChunker:
    """
    Handles semantic chunking of ticket data for RAG.
    """

    def __init__(self, max_chunk_size: int = 512, overlap: int = 50):
        """
        Initialize chunker.

        Args:
            max_chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, chunk_type: str = "description") -> List[str]:
        """
        Split text into semantic chunks.

        Strategy:
        1. Split by paragraphs (double newline)
        2. Split by sentences if paragraph too long
        3. Split by words if sentence too long
        """
        if not text or len(text) <= self.max_chunk_size:
            return [text] if text else []

        chunks = []

        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds limit, save current chunk
            if len(current_chunk) + len(para) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If paragraph itself is too long, split by sentences
                if len(para) > self.max_chunk_size:
                    sentences = re.split(r'[.!?]+\s+', para)
                    temp_chunk = ""

                    for sent in sentences:
                        if len(temp_chunk) + len(sent) > self.max_chunk_size:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = sent
                        else:
                            temp_chunk += (". " if temp_chunk else "") + sent

                    current_chunk = temp_chunk
                else:
                    current_chunk = para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def create_ticket_chunks(self, ticket_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create searchable chunks from a ticket.

        Returns list of chunk documents for Elasticsearch indexing.
        Each chunk includes parent ticket metadata for reconstruction.
        """
        chunks = []
        ticket_id = ticket_data["ticket_id"]

        # Chunk 0: Summary (always keep as single chunk)
        if ticket_data.get("summary"):
            chunks.append({
                "chunk_id": f"{ticket_id}_summary",
                "parent_ticket_id": ticket_id,
                "chunk_type": "summary",
                "chunk_number": 0,
                "content": ticket_data["summary"],
                "ultimate_sentiment": ticket_data.get("ultimate_sentiment"),
                "confidence": ticket_data.get("confidence"),
                "entities": ticket_data.get("entities", []),
                "created_at": ticket_data.get("created_at")
            })

        # Chunks 1+: Description (split if long)
        if ticket_data.get("description"):
            desc_chunks = self.chunk_text(ticket_data["description"], "description")
            for idx, chunk_text in enumerate(desc_chunks, start=1):
                chunks.append({
                    "chunk_id": f"{ticket_id}_desc_{idx}",
                    "parent_ticket_id": ticket_id,
                    "chunk_type": "description",
                    "chunk_number": idx,
                    "content": chunk_text,
                    "ultimate_sentiment": ticket_data.get("ultimate_sentiment"),
                    "confidence": ticket_data.get("confidence"),
                    "entities": ticket_data.get("entities", []),
                    "created_at": ticket_data.get("created_at")
                })

        # Chunks for comments (if available)
        if ticket_data.get("comments"):
            comments = ticket_data["comments"]
            if isinstance(comments, list):
                for idx, comment in enumerate(comments[:10], start=100):  # Max 10 comments
                    if isinstance(comment, dict):
                        comment_text = comment.get("text", "")
                    else:
                        comment_text = str(comment)

                    if comment_text:
                        chunks.append({
                            "chunk_id": f"{ticket_id}_comment_{idx}",
                            "parent_ticket_id": ticket_id,
                            "chunk_type": "comment",
                            "chunk_number": idx,
                            "content": comment_text[:self.max_chunk_size],  # Limit comment length
                            "ultimate_sentiment": ticket_data.get("ultimate_sentiment"),
                            "confidence": ticket_data.get("confidence"),
                            "entities": ticket_data.get("entities", []),
                            "created_at": ticket_data.get("created_at")
                        })

        return chunks

    def reconstruct_ticket_context(self, chunks: List[Dict[str, Any]], max_chars: int = 2000) -> str:
        """
        Reconstruct ticket context from retrieved chunks.

        Args:
            chunks: List of chunk documents from Elasticsearch
            max_chars: Maximum total characters for context

        Returns:
            Formatted context string
        """
        # Group chunks by parent ticket
        tickets = {}
        for chunk in chunks:
            ticket_id = chunk.get("parent_ticket_id") or chunk.get("ticket_id")
            if ticket_id not in tickets:
                tickets[ticket_id] = {
                    "ticket_id": ticket_id,
                    "summary": None,
                    "description_parts": [],
                    "comments": [],
                    "sentiment": chunk.get("ultimate_sentiment") or chunk.get("sentiment"),
                    "score": chunk.get("score", 0)
                }

            chunk_type = chunk.get("chunk_type", "")
            content = chunk.get("content", "")

            if chunk_type == "summary":
                tickets[ticket_id]["summary"] = content
            elif chunk_type == "description":
                tickets[ticket_id]["description_parts"].append(content)
            elif chunk_type == "comment":
                tickets[ticket_id]["comments"].append(content)

        # Build context string
        context_parts = []
        total_chars = 0

        for idx, (ticket_id, ticket_info) in enumerate(tickets.items(), 1):
            ticket_context = f"\n**Ticket #{idx}** (ID: {ticket_id}, Sentiment: {ticket_info['sentiment']})\n"

            if ticket_info["summary"]:
                ticket_context += f"Summary: {ticket_info['summary']}\n"

            if ticket_info["description_parts"]:
                desc = " ".join(ticket_info["description_parts"])
                ticket_context += f"Description: {desc[:800]}{'...' if len(desc) > 800 else ''}\n"

            if ticket_info["comments"]:
                ticket_context += f"Comments ({len(ticket_info['comments'])}): "
                ticket_context += " | ".join(ticket_info["comments"][:3])  # Show first 3 comments
                ticket_context += "\n"

            ticket_context += "---\n"

            # Check if adding this ticket exceeds limit
            if total_chars + len(ticket_context) > max_chars:
                break

            context_parts.append(ticket_context)
            total_chars += len(ticket_context)

        return "".join(context_parts)


# Global instance
rag_chunker = RAGChunker(max_chunk_size=512, overlap=50)
