import re
import json
import pickle
from html import unescape

from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain.chains import GraphQAChain
from langchain.prompts import PromptTemplate
from langchain_community.graphs.index_creator import GraphIndexCreator
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph,KnowledgeTriple


import networkx as nx
#from langchain.graphs.networkx_graph import KG_TRIPLE_DELIMITER
from typing import List, Tuple
import re

from langchain_text_splitters import CharacterTextSplitter,TokenTextSplitter

def remove_sections(text, blacklist):
    """Removes entire sections based on header names"""
    # Split text into sections using header markers
    sections = re.split(r'(?m)^(==+)\s*(.*?)\s*\1\s*$', text)
    if len(sections) < 2:
        return text
    
    # Process sections: [lead, header_marker, header, header_marker, content, ...]
    cleaned_sections = []
    current_header = None
    
    # Always keep the lead section (content before first header)
    cleaned_sections.append(sections[0])
    
    # Process subsequent sections
    for i in range(1, len(sections), 3):
        if i + 2 >= len(sections):
            break
            
        header_marker = sections[i]
        header = sections[i+1]
        content = sections[i+2]
        
        # Normalize header for comparison
        normalized_header = header.strip().lower()
        
        # Keep section if not in blacklist
        if normalized_header not in blacklist:
            cleaned_sections.append(header_marker)
            cleaned_sections.append(header)
            cleaned_sections.append(header_marker)
            cleaned_sections.append(content)
    
    return ''.join(cleaned_sections)

def clean_page(uncleaned : dict, section_blacklist: list = None):
    clean_content = {}
    if section_blacklist is None:
        section_blacklist = ['gallery',
                        'soundtrack',
                        'videos', 
                        'trivia',
                        'references',
                        'title updates'
                        ]
    for page,content in uncleaned.items():
        # Convert to lowercase for case-insensitive matching
        section_blacklist = [s.lower() for s in section_blacklist]
        # cleaned = enhanced_clean_wiki_text(content)
        cleaned = remove_sections(content, section_blacklist)
        # Remove references and URLs
        cleaned = re.sub(r'\[\d+\]', '', cleaned)  # [1], [2] style references
        cleaned = re.sub(r'\[https?://[^\s]+\s+([^\]]+)\]', r'\1', cleaned)  # [http://... Label]
        cleaned = re.sub(r'https?://\S+', '', cleaned)  # Bare URLs

        # Remove all {{templates}} including multi-line templates
        cleaned = re.sub(r'\{\{.*?\}\}', '', cleaned, flags=re.DOTALL)
        #cleaned = clean_wiki_text(content)
        clean_content[page] = cleaned
    return clean_content

def graph_builder(clean_text : dict):
        index_creator = GraphIndexCreator(llm=OllamaLLM(model="qwen2.5:14b"))
        graph = NetworkxEntityGraph()
        triples = []
        for page,text in clean_text.items():
            temp_graph = index_creator.from_text(text)
            triples = triples + temp_graph.get_triples()

        with open('my_list.pkl', 'wb') as file:
            pickle.dump(triples, file)
        
        for triple in triples:
            triple = KnowledgeTriple(triple[0],triple[1],triple[2])
            graph.add_triple(triple)
        graph.write_to_gml("Division2_knowledge.gml")

if __name__ == "__main__":
    # Your sample text here
    with open("wiki_content.json","r") as f:
        uncleaned = json.load(f)


    # with open('my_list.pkl', 'rb') as file:
    #     loaded_list = pickle.load(file)
    # print(loaded_list)
    # exit()

    # clean_text = clean_page(uncleaned)
    # graph_builder(clean_text)
    
    
    index_creator = GraphIndexCreator(llm=OllamaLLM(model="qwen2.5:14b"))

    text = """Alani Kelso, callsign Cassandra, is a Division agent who was assigned to Washington, D.C. to help retake. With the advent of several Division agents who came to the city, she played a major part in coordinating efforts and assisting agents in the field with restoring the SHD Network and retaking the Capitol.
    Kelso was also involved in the events of Warlords of New York, where she helped the agents neutralize Aaron Keener and his cell in Lower Manhattan in addition to helping agents in the Manhunts against Rogue Cells. The revelation of Faye Lau, a fellow agent who went rogue after WONY's campaign, shook her heavily And as such, she disavowed Lau as a traitor and was involved in the Manhunt that led to her death.
    However, recent events have put Kelso to a difficult position, where she learned that Lau and Schaeffer were helping the Division the whole time and trying to prove Lau's innocence to a lot of people. In Vanguard, she went missing when she followed the trail that led her to Keener and Theo Parnell.
    After being shown the truth from both of them, Kelso joined with them and escaped New York via a van after Keener recovered a Mobile SHD Server, with their destination set for their Washington, D.C. to parley with the Division. Her partnership with them marked her as Rogue.
    In First Rogue, Kelso was forced to separate from her team when they were ambushed by a Black Tusk's "welcoming party" after they arrived to the capitol. While the Division managed to locate and secure Keener and Parnell to the White House, Kelso was still in hiding.
    In Burden of Truth, as Division agents followed the clues that Kelso scattered across Washington D.C, they uncovered more truth behind Faye Lau, the Cassandra mission, and Bardon Schaeffer. """
    
    text2 = """Aaron Keener, callsign Vanguard, is a First Wave Strategic Homeland Division agent who, after the Joint Task Force's disastrous
    surrender and retreat from the Dark Zone, disavowed the Division and went rogue. Recruiting a number of other First Wave agents to his cause
    and killing those who resisted, he developed his own ambitions for establishing order and a future for the country or possibly the world, 
    even if he is accused of high treason and branded a traitor of the United States federal government to do it.
    While Keener's identity was shrouded throughout Tom Clancy's The Division, his intentions were unraveled during the events
    of Warlords of New York, making him somewhat of an antagonist whose intentions were far worse than that of Gordon Amherst.
    In Year 6 Season 1: First Rogue, after he survived his encounter with the Division at Liberty Island. Keener went to D.C. to parley with them 
    and build up an alliance against Black Tusk and the Hunters. Since then, the agents secured Keener, and he was put in house arrest at the 
    White House's Panic Room, while the Division worked in finding Theo Parnell and Alani Kelso before he could share more of what he knows."""
    
    text_splitter = TokenTextSplitter(
    # Controls the size of each chunk
    chunk_size=2000,
    # Controls overlap between chunks
    chunk_overlap=20,
    )   

    import re

    def estimate_token_count(input_string):
        # Tokenize the string into words and punctuation using regex
        tokens = re.findall(r'\b\w+\b|[^\w\s]', input_string)
        return len(tokens)

    print(estimate_token_count(uncleaned["Alani Kelso"]))
    sumarizer = OllamaLLM(model="qwen3:14b",num_ctx=2048*5,think=False)
    sumarize_prompt = """
    **Role:** You are text reviewer and
    **Task:** Review and summarize the provided text. Your output must include the following sections:

    1.  **Key Points (Bulleted List):** 
        -   Extract core ideas, arguments, or findings.
        -   Focus on essential concepts, not minor details.

    2.  **Overall Summary (Verbose Paragraph):**
        -   Synthesize the key points into detailed summary including all the information 
            in the given text with as much detail as possible
        

**Additional Instructions:**
*   **Be Objective:** Represent the text faithfully. Distinguish facts from opinions stated *in* the text.
*   **Maintain identity:** When dealing with people always use the first appeareance of their full name to refer to them.
*   **Be verbose:** Prioritize lenght and giving as much deatial as possible while maintaining accuracy.
*   **Adapt Tone (Optional):** Tailor the summary tone slightly if needed (e.g., more formal for academic text, simpler for casual content). Default is neutral.
*   **Handle Length:** If the text is very long, focus on the most significant sections or provide a high-level overview first. 
                        Then give different sections for more specific topics

**(Text will be provided after this prompt)**

**Text to Analyze:**

    """
    sumarize_prompt = sumarize_prompt +"\n\n" +uncleaned["Alani Kelso"]
    response = sumarizer.invoke(sumarize_prompt)
    print(response)

    # print(uncleaned["Alani Kelso"])
    # texts = text_splitter.split_text(text)
    # print(texts)
    # print("="*80)
    # texts = text_splitter.split_text(text2)
    # print(texts)
    # graphAK = index_creator.from_text(text)
    # graphFR = index_creator.from_text(text2)
    # graph = NetworkxEntityGraph.from_gml('Division2_knowledge.gml')
    
    # chainAK = GraphQAChain.from_llm(OllamaLLM(model="qwen2.5:14b"), graph=graphAK, verbose=True)
    # chainFR = GraphQAChain.from_llm(OllamaLLM(model="qwen2.5:14b"), graph=graphFR, verbose=True)
    # chain = GraphQAChain.from_llm(OllamaLLM(model="qwen2.5:14b"), graph=graph, verbose=True)

    # context = chainFR.invoke("Give me a summary about Aaron Keener.")
    # print(context)
    # print("+"*80)
    # context = chainAK.invoke("Who is Alani Kelso?")
    # print(context)
    # print("+"*80)
    # print("="*80)
    # context = chain.invoke("Who is Alani Kelso?")
    # print(context)
    # context = chain.invoke("What can you tell me about Kelso?")
    # print("="*80)
    # context = chain.invoke("Give me a summary about Aaron Keener.")
    # print(context)

    # triples = kg_builder.extract_triples(text)
    
    # print("Extracted Triples:")
    # for i, (s, p, o) in enumerate(triples, 1):
    #     print(f"{i}. {s} -- {p} --> {o}")
    