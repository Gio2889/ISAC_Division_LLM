import json
from pydantic import BaseModel
from ollama import ChatResponse, chat
from typing import List, Dict, Any
import tiktoken
TOKENIZER_NAME = "o200k_base"
def route_chunks(question: str, chunks: List[Dict[str, Any]], 
                depth: int, scratchpad: str = "") -> Dict[str, Any]:
    """
    Ask the model which chunks contain information relevant to the question.
    Maintains a scratchpad for the model's reasoning.
    Uses structured output for chunk selection and required tool calls for scratchpad.
    
    Args:
        question: The user's question
        chunks: List of chunks to evaluate
        depth: Current depth in the navigation hierarchy
        scratchpad: Current scratchpad content
    
    Returns:
        Dictionary with selected IDs and updated scratchpad
    """
    
    print(f"\n==== ROUTING AT DEPTH {depth} ====")
    print(f"Evaluating {len(chunks)} chunks for relevance")
    tokenizer = tiktoken.get_encoding(TOKENIZER_NAME)
    # Build system message
    system_message = """You are an expert document navigator. Your task is to:
1. Identify which text chunks might contain information to answer the user's question
2. Record your reasoning in a scratchpad for later reference
3. Choose chunks that are most likely relevant. Be selective, but thorough. Choose as many chunks as you need to answer the question, but avoid selecting too many.

First think carefully about what information would help answer the question, then evaluate each chunk. 
Use literal information in the chunks, do not make any assumptions, if no helpful information in the chunk, say so.
Do make any knowledge inferences.
"""

    # Build user message with chunks and current scratchpad
    user_message = f"QUESTION: {question}\n\n"
    
    if scratchpad:
        user_message += f"CURRENT SCRATCHPAD:\n{scratchpad}\n\n"
    
    user_message += "TEXT CHUNKS:\n\n"
    
    # Add each chunk to the message
    for chunk in chunks:
        user_message += f"CHUNK {chunk['id']}:\n{chunk['text']}\n\n"
    
    # Define function schema for scratchpad tool calling
    update_scratchpad = {
            "type": "function",
            'function': {
                "name": "update_scratchpad",
                "description": "Record your reasoning about why certain chunks were selected",
                #"strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Your reasoning about the chunk(s) selection"
                            }
                    },
                    "required": ["text"],
                    #"additionalProperties": False
                }
            }
    }
    tools = [update_scratchpad]
    
    # Define JSON schema for structured output (selected chunks)
    text_format = {
        "format": {
            "type": "json_schema",
            "name": "selected_chunks",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "chunk_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "IDs of the selected chunks that contain information to answer the question"
                    }
                },
                "required": [
                    "chunk_ids"
                ],
                "additionalProperties": False
            }
        }
    }
    
    available_functions = {"update_scratchpad": update_scratchpad}
    # First pass: Call the model to update scratchpad (required tool call)
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message + "\n\nFirst, you must use the update_scratchpad function to record your reasoning."}
    ]
    
    print(f" messages has: {len(tokenizer.encode(user_message))} tokens")
    try:
        response : ChatResponse = chat(
            model="qwen2.5:14b_32k",
            messages=messages,
            tools=tools,
            #tool_choice="required"
        )
        print(response)
    except Exception as e:
        print(f"Error on Ollama call {e}")
    # Process the scratchpad tool call
    new_scratchpad = scratchpad
    print(response.message.tool_calls)

    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            # Ensure the function is available, and then call it
            if available_functions.get(tool.function.name): #checks if the tool is available
                print('Calling function:', tool.function.name)
                #print('Arguments:', tool.function.arguments)
                args = json.loads(json.dumps(tool.function.arguments))
                scratchpad_entry = f"DEPTH {depth} REASONING:\n{args.get('text', '')}"
                # output = function_to_call(**tool.function.arguments)
                #print('Function output:\n', scratchpad_entry)
                
                if new_scratchpad:
                    new_scratchpad += "\n\n" + scratchpad_entry
                else:
                    new_scratchpad = scratchpad_entry
                
                messages.append(response.message)
                messages.append({
                                'role': 'tool',
                                'content': "Scratchpad updated successfully.",
                                'name': tool.function.name
                                })
            else:
                print('Function', tool.function.name, 'not found')   
    else:
        print("--- Error no tools available---")
    #--------------------------- First pass end --------------------------#
    class BaseInfo(BaseModel):
        # document_idx : int 
        chunk_id : int

    class ChunkInfo(BaseModel):
        chunk_ids : list[BaseInfo]
    # Second pass: Get structured output for chunk selection
    messages.append({"role": "user", "content": "Now, select the chunks that could contain information to answer the question. Return a JSON object with the list of chunk IDs. Do make any knoledge inferences. If there no helpfull chunks return an empty list"})
    
    # print(f"Current mesasge passed to model:\n {messages}")
    response_chunks : ChatResponse = chat(
        model="qwen2.5:14b",
        messages=messages,
        format=ChunkInfo.model_json_schema()
    )
    selected_ids = []
    if response_chunks.message.content:
        try:
            # The output_text should already be in JSON format due to the schema
            chunk_data = response_chunks.message.content
            selected_ids = json.loads(chunk_data)["chunk_ids"]
            #selected_ids = chunk_data.get("chunk_ids", [])
        except json.JSONDecodeError:
            print("Warning: Could not parse structured output as JSON")
    
    # Display results
    print(f"Selected chunks: {', '.join(str(id) for id in selected_ids)}")
    print(f"Updated scratchpad:\n{new_scratchpad}")
    
    return {
        "selected_ids": selected_ids,
        "scratchpad": new_scratchpad
    }


if __name__ == "__main__":
    from Local_chunk_edits.TextChunker import split_into_20_chunks
    with open("src/data/scraped_data_v01.json",'r') as f:
        data = json.load(f)
    all_data = ""
    for item in data[16:60]:
        if all_data:
            all_data = all_data + "\n\n" + item["content"]
        else:
            all_data = item["content"]

    query = "Who is Alani Kelso?"
    chunks = split_into_20_chunks(all_data)
    chunk_info = route_chunks(query,chunks,1)
    print(chunk_info)
    scratchpad = ""
    # k=0
    # for item in data[16:]:
    #     if not isinstance(item, dict):
    #         print("--- Error with item: ---\n {item}")
    #     print(f"--- Chunking {item['source']} ---")
    #     chunks = split_into_20_chunks(item['content'])
    #     chunk_info = route_chunks(query,chunks,1)
    #     if chunk_info:
    #         selected_chunks = chunk_info["selected_ids"] 
    #         if selected_chunks:
    #             scratchpad += "\n\n" + chunk_info["scratchpad"]
    #     else:
    #         print("--- No response from chunk evaluation ---")
    #     if k>3:
    #         exit()
    #     k+=1

print("--- final scratch pad ---")
print(scratchpad)



