from typing import Dict,Any
from TextChunker import split_into_20_chunks
from ChunkRouter import route_chunks

import json 
import re
import tiktoken
def navigate_to_paragraphs(document_text: str, question: str, max_depth: int = 1) -> Dict[str, Any]:
    """
    Navigate through the document hierarchy to find relevant paragraphs.
    
    Args:
        document_text: The full document text
        question: The user's question
        max_depth: Maximum depth to navigate before returning paragraphs (default: 1)
    
    Returns:
        Dictionary with selected paragraphs and final scratchpad
    """
    scratchpad = ""
    
    # Get initial chunks with min 500 tokens
    chunks = split_into_20_chunks(document_text, min_tokens=500)
    
    # Navigator state - track chunk paths to maintain hierarchy
    chunk_paths = {}  # Maps numeric IDs to path strings for display
    for chunk in chunks:
        chunk_paths[chunk["id"]] = str(chunk["id"])
    
    # Navigate through levels until max_depth or until no chunks remain
    for current_depth in range(max_depth + 1):
        # Call router to get relevant chunks
        result = route_chunks(question, chunks, current_depth, scratchpad)
        
        # Update scratchpad
        scratchpad = result["scratchpad"]
        
        # Get selected chunks
        selected_ids = result["selected_ids"]
        selected_chunks = [c for c in chunks if c["id"] in selected_ids]
        
        # If no chunks were selected, return empty result
        if not selected_chunks:
            print("\nNo relevant chunks found.")
            return {"paragraphs": [], "scratchpad": scratchpad}
        
        # If we've reached max_depth, return the selected chunks
        if current_depth == max_depth:
            print(f"\nReturning {len(selected_chunks)} relevant chunks at depth {current_depth}")
            
            # Update display IDs to show hierarchy
            for chunk in selected_chunks:
                chunk["display_id"] = chunk_paths[chunk["id"]]
                
            return {"paragraphs": selected_chunks, "scratchpad": scratchpad}
        
        # Prepare next level by splitting selected chunks further
        next_level_chunks = []
        next_chunk_id = 0  # Counter for new chunks
        
        for chunk in selected_chunks:
            # Split this chunk into smaller pieces
            sub_chunks = split_into_20_chunks(chunk["text"], min_tokens=200)
            
            # Update IDs and maintain path mapping
            for sub_chunk in sub_chunks:
                path = f"{chunk_paths[chunk['id']]}.{sub_chunk['id']}"
                sub_chunk["id"] = next_chunk_id
                chunk_paths[next_chunk_id] = path
                next_level_chunks.append(sub_chunk)
                next_chunk_id += 1
        
        # Update chunks for next iteration
        chunks = next_level_chunks

if __name__ == '__main__':
    with open("src/data/scraped_data_v01.json",'r') as f:
        data = json.load(f)
    all_data = ""
    for item in data:
        if all_data:
            all_data = all_data + "\n\n" + item["content"]
        else:
            all_data = item["content"]

    word_count = len(re.findall(r'\b\w+\b', all_data))
    
    tokenizer = tiktoken.get_encoding("o200k_base")
    token_count = len(tokenizer.encode(all_data))
    print(f"total token counts {token_count}")
    question = "Who is Alani Kelso?"

    navigation_result = navigate_to_paragraphs(all_data, question, max_depth=2)

    # Sample retrieved paragraph
    print("\n==== FIRST 3 RETRIEVED PARAGRAPHS ====")
    for i, paragraph in enumerate(navigation_result["paragraphs"][:3]):
        display_id = paragraph.get("display_id", str(paragraph["id"]))
        print(f"\nPARAGRAPH {i+1} (ID: {display_id}):")
        print("-" * 40)
        print(paragraph["text"])
        print("-" * 40)