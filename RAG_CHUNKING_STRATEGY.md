# RAG Chunking Strategy for Support Tickets

## Current Status (Before Chunking)

❌ **Issues:**
- Full tickets indexed as single documents
- Descriptions truncated to 500 chars
- Comments not included in RAG context
- Poor context utilization (only 5 tickets, ~2500 chars)

## New Chunking Strategy

### ✅ Improvements:

1. **Semantic Chunking** (512 chars per chunk with 50 char overlap)
   - Split by paragraphs first
   - Split by sentences if paragraph too long
   - Maintain context continuity with overlap

2. **Chunk Types:**
   - `summary` - Always single chunk (most important)
   - `description` - Split into multiple chunks if needed
   - `comment` - Individual comments as chunks (max 10)

3. **Metadata Preservation:**
   ```json
   {
     "chunk_id": "TICKET-123_desc_2",
     "parent_ticket_id": "TICKET-123",
     "chunk_type": "description",
     "chunk_number": 2,
     "content": "...",
     "ultimate_sentiment": "negative",
     "entities": [...]
   }
   ```

4. **Smart Retrieval:**
   - Retrieve relevant chunks (not full tickets)
   - Group by parent_ticket_id to avoid duplication
   - Reconstruct context up to 2000 chars
   - Include comments for richer context

## Context Window Utilization

**Llama 2 70B:** 4096 tokens (~16,384 characters)

**Allocation:**
- System prompt + instructions: ~1,000 chars (250 tokens)
- Aggregate statistics: ~500 chars (125 tokens)
- Retrieved ticket context: **~2,000 chars** (500 tokens) ← IMPROVED
- User query: ~200 chars (50 tokens)
- **Total:** ~3,700 chars (~925 tokens)
- **Remaining:** ~12,684 chars for response

## Benefits

1. **Better Relevance**: Retrieve specific paragraphs/comments matching query
2. **More Context**: Fit more relevant information in same space
3. **Include Comments**: Previously missing from RAG
4. **Reduced Truncation**: Smart semantic boundaries instead of character limits
5. **Scalability**: Works with very long tickets (split into manageable chunks)

## Implementation Files

- `backend/services/rag_chunker.py` - Chunking logic
- `backend/services/elasticsearch_client.py` - Index chunks
- `backend/api/nlq_api.py` - Use chunks for RAG

## Usage

### Option 1: Current Approach (No Chunking)
```python
# Works but suboptimal
es_client.index_ticket(ticket_data)
```

### Option 2: With Chunking (Recommended)
```python
from backend.services.rag_chunker import rag_chunker

chunks = rag_chunker.create_ticket_chunks(ticket_data)
for chunk in chunks:
    es_client.index_chunk(chunk)  # Index each chunk separately
```

### Retrieval with Chunks
```python
# Retrieve relevant chunks
chunks = es_client.search_chunks(query, limit=20)

# Reconstruct context
context = rag_chunker.reconstruct_ticket_context(chunks, max_chars=2000)
```

## Migration Path

### Phase 1: Current (Deployed) ✅
- Full ticket indexing
- Basic RAG with 500 char truncation
- Works but not optimal

### Phase 2: Enhanced (Next Step)
- Implement chunked indexing
- Update retrieval to use chunks
- Re-index existing tickets with chunking
- Better context utilization

### Phase 3: Advanced (Future)
- Vector embeddings for semantic search
- Hybrid search (BM25 + vectors)
- Dynamic chunk sizing based on content
- Query expansion and reranking

## Quick Win

For now, the **current approach works** for support tickets because:
- Most descriptions are reasonably short (< 2000 chars)
- Summaries are always concise
- 5-10 tickets fit well in context window

But **chunking will significantly improve**:
- Tickets with very long descriptions
- Multi-comment tickets
- Queries needing specific details from long text
- Overall context quality and relevance

## Next Steps

1. Test current sync completion (10,003 tickets)
2. Run NLQ query to see RAG with real data
3. Optionally implement chunked re-indexing for better results
4. Monitor context quality and adjust chunk size if needed
