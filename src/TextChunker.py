# Global tokenizer name to use consistently throughout the code
import tiktoken
import nltk 
from nltk.tokenize import sent_tokenize
from typing import List, Dict, Any
import json
nltk.download('punkt_tab')
TOKENIZER_NAME = "o200k_base"

def split_into_20_chunks(text: str, min_tokens: int = 500) -> List[Dict[str, Any]]:
    """
    Split text into up to 20 chunks, respecting sentence boundaries and ensuring
    each chunk has at least min_tokens (unless it's the last chunk).
    
    Args:
        text: The text to split
        min_tokens: The minimum number of tokens per chunk (default: 500)
    
    Returns:
        A list of dictionaries where each dictionary has:
        - id: The chunk ID (0-19)
        - text: The chunk text content
    """
    # First, split the text into sentencess
    sentences = sent_tokenize(text)
    
    # Get tokenizer for counting tokens
    tokenizer = tiktoken.get_encoding(TOKENIZER_NAME)
    
    # Create chunks that respect sentence boundaries and minimum token count
    chunks = []
    current_chunk_sentences = []
    current_chunk_tokens = 0
    
    for sentence in sentences:
        # Count tokens in this sentence
        sentence_tokens = len(tokenizer.encode(sentence))
        
        # If adding this sentence would make the chunk too large AND we already have the minimum tokens,
        # finalize the current chunk and start a new one
        if (current_chunk_tokens + sentence_tokens > min_tokens * 2) and current_chunk_tokens >= min_tokens:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "id": len(chunks),  # Integer ID instead of string
                "text": chunk_text
            })
            current_chunk_sentences = [sentence]
            current_chunk_tokens = sentence_tokens
        else:
            # Add this sentence to the current chunk
            current_chunk_sentences.append(sentence)
            current_chunk_tokens += sentence_tokens
    
    # Add the last chunk if there's anything left
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        chunks.append({
            "id": len(chunks),  # Integer ID instead of string
            "text": chunk_text
        })
    
    # If we have more than 20 chunks, consolidate them
    if len(chunks) > 20:
        # Recombine all text
        all_text = " ".join(chunk["text"] for chunk in chunks)
        # Re-split into exactly 20 chunks, without minimum token requirement
        sentences = sent_tokenize(all_text)
        sentences_per_chunk = len(sentences) // 20 + (1 if len(sentences) % 20 > 0 else 0)
        
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            # Get the sentences for this chunk
            chunk_sentences = sentences[i:i+sentences_per_chunk]
            # Join the sentences into a single text
            chunk_text = " ".join(chunk_sentences)
            # Create a chunk object with ID and text
            chunks.append({
                "id": len(chunks),  # Integer ID instead of string
                "text": chunk_text
            })
    
    # Print chunk statistics
    print(f"Split document into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        token_count = len(tokenizer.encode(chunk["text"]))
        print(f"Chunk {i}: {token_count} tokens")
    
    return chunks

if __name__ == "__main__":
    with open("data/scraped_data_v01.json",'r') as f:
        data = json.load(f)
    
    for item in data[::10]:
        print(f"--- Chunking {item['source']} ---")
        split_into_20_chunks(item['content'])
    