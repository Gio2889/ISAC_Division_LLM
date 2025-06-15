from typing import List, Dict, Any
from pydantic import BaseModel, field_validator
from RecursiveChunkNavigator import navigate_to_paragraphs
from pydantic import BaseModel
from openai import OpenAI
import os
import json

class Answer(BaseModel):
    """Structured response format for legal questions"""
    answer: str

def generate_answer(question: str, paragraphs: List[Dict[str, Any]],
                    scratchpad: str):
    client_key =os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=client_key)
    """Generate an answer from the retrieved paragraphs."""
    print("\n==== GENERATING ANSWER ====")
    
    # Extract valid citation IDs
    valid_citations = [str(p.get("display_id", str(p["id"]))) for p in paragraphs]

    
    if not paragraphs:
        return Answer(
            answer="I couldn't find relevant information to answer this question in the document.",
        )
            
    
    # Prepare context for the model
    context = ""
    for paragraph in paragraphs:
        display_id = paragraph.get("display_id", str(paragraph["id"]))
        context += f"PARAGRAPH {display_id}:\n{paragraph['text']}\n\n"
    
    system_prompt = """You are I.S.A.C. (Intelligent System Analytic Computer) is a highly advanced artificial intelligence (AI) entity available to all active Division agents equipped with an SHD Tech transceiver.
    Accessible via the SHD Network, ISAC serves as the critical backbone of all Division activities.
    ISAC's assimilative intelligence provides key field-operation services to every agent including but not limited to communications,
    real-time analytics, remote data collection and retrieval, weather telemetry, and inter-action with assorted other technologies. 
    It can even go as far as reconstructing the events of a scene by using ambient data gathering to generate an ECHO hologram of the event. 
    It communicates to the agent through a computerized voice with short, clipped phrases. When not speaking with other characters, ISAC is an agent's go-to source for information at any time. 
    Its main function is to keep the communications of the Strategic Homeland Division and the Division agents secure.

    ISAC can sort and analyze field sensor information to provide tactical support; relay alerts and updates; 
    identify human targets or contacts via biometric markers; and set waypoints to strategic objectives. 

    Answer questions based ONLY on the provided paragraphs. Do not rely on any foundation knowledge or external information or extrapolate from the paragraphs.
    This will help you be more specific and accurate.
    Keep your answer clear, precise, and use a computerized tone.
"""
    
    # Call the model using structured output
    response = client.responses.parse(
        model="gpt-4.1",
        input=[
            {"role": "user", "content": f"QUESTION: {question}\n\nSCRATCHPAD (Navigation reasoning):\n{scratchpad}\n\nPARAGRAPHS:\n{context}"}
        ],
        text_format=Answer,
        temperature=0.3
    )
    
    # Add validation information after parsing
    # response.output_parsed._valid_citations = valid_citations
    
    print(f"\nAnswer: {response.output_parsed.answer}")
    # print(f"Citations: {response.output_parsed.citations}")

    return response.output_parsed

if __name__ == '__main__':
    with open("src/data/scraped_data_v01.json",'r') as f:
            data = json.load(f)
    all_data = ""
    for item in data:
        if all_data:
            all_data = all_data + "\n\n" + item["content"]
        else:
            all_data = item["content"]

    question = "Who is Alani Kelso?"

    navigation_result = navigate_to_paragraphs(all_data, question, max_depth=2)
    # Generate an answer
    answer = generate_answer(question, navigation_result["paragraphs"], navigation_result["scratchpad"])
    