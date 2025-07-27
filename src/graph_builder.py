import re
import json
from langchain_ollama import OllamaLLM
from typing import List, Tuple
from langchain_community.chains.graph_qa.base import GraphQAChain
from langchain_core.language_models import BaseLLM
from langchain_community.graphs.index_creator import GraphIndexCreator
from langchain_community.graphs.networkx_graph import (
    NetworkxEntityGraph,
    KnowledgeTriple,
)
from langchain_text_splitters import CharacterTextSplitter


class graph_builder:
    def __init__(
        self,
        main_llm: BaseLLM = None,
        chain_llm: BaseLLM = None,
        test: bool = False,
        graph_name: str = "Division2_graph.gml",
    ):
        self.text_spliter = CharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base", chunk_size=100, chunk_overlap=0
        )
        self.SUMARIZER_PROMPT = """
            **Role:** You are text reviewer and
            **Task:** Review and summarize the provided text. Your output must include the following sections:

            1.  **Key Points (Bulleted List):** 
                -   Extract core ideas, arguments, or findings.
                -   Focus on essential concepts, not minor details.

            2.  **Overall Summary (Verbose Paragraph):**
                -   Synthesize the key points into detailed summary including all the information 
                    in the given text with as much detail as possible.
                
            **Additional Instructions:**
            *   **Be Objective:** Represent the text faithfully. Distinguish facts from opinions stated *in* the text.
            *   **Maintain identity:** When dealing with people always use the first appeareance of their full name to refer to them.
            *   **Be verbose:** Prioritize lenght and giving as much deatial as possible while maintaining accuracy.
            *   **Adapt Tone (Optional):** Tailor the summary tone slightly if needed (e.g., more formal for academic text, simpler for casual content). Default is neutral.
            *   **Handle Length:** If the text is very long, focus on the most significant sections or provide a high-level overview first. Then give different sections for more specific topics
            *   **Naming conventions:** When a person or place is refere in the text always use the most complete name you can. 

            **(Text will be provided after this prompt)**

            **Text to Analyze:**
        """

        self.model_ctx = 30000
        if test:
            # adds seed and lowers temp for testing purposes
            llm_params = {
                "num_ctx": self.model_ctx,
                "reasoning": False,
                "seed": 42420,
                "temperature": 0,
            }
        else:
            llm_params = {
                "num_ctx": self.model_ctx,
                "reasoning": False,
            }

        # set defaults for LLMs
        if main_llm is None:
            # add default model for main LLM
            llm_params["model"] = "qwen3:14b"
            self.main_llm = OllamaLLM(**llm_params)
        else:
            self.main_llm = main_llm

        if chain_llm is None:
            # add default model for chain LLM
            llm_params["model"] = "qwen2.5:14b"
            self.chain_llm = OllamaLLM(**llm_params)
        else:
            self.chain_llm = chain_llm

        # create index for extracting knowledge triples
        self.index_creator = GraphIndexCreator(llm=self.llm_main)

        # list for all the triples to build the final graph
        self.all_triples = []

        # graph variables
        self.save_graph = True
        self.graph_name = graph_name
        self.graph = None

        # main chain for quering graph
        self.chain = None

    def ingest(self, raw_data: dict):
        """ingest scrapped data the function cleans the data, then creates
        knowledge triples for each element until a full graph is created
        """
        for element, page in raw_data:
            clean_data = self._clean_page(page)
            # pass the cleaned page data to the llm along with the summarizer prompt
            full_prompt = self.SUMARIZER_PROMPT + "\n" + clean_data
            estimated_tokens = self.__estimate_token_count(full_prompt)
            if estimated_tokens > self.model_ctx:
                print("Data might be incomplete due to the context leght of the model.")
            ######################################
            # todo create a chunking strategy here
            ######################################
            page_summary = self.main_llm.invoke(full_prompt)
            new_triples = self._get_triples(page_summary)
            # update the full list of triples
            self.all_triples = self.all_triples + new_triples

        # build graph wiht all known triples
        self.graph = self._graph_builder(self.all_triples)

        # set up chain for querying
        self.chain = GraphQAChain.from_llm(
            self.chain_llm, graph=self.graph, verbose=True
        )

    def query(self, query_str: str):
        if self.chain is None:
            try:
                self.graph = NetworkxEntityGraph.from_gml(self.graph_name)
                self.chain = GraphQAChain.from_llm(
                    self.chain_llm, graph=self.graph, verbose=True
                )
            except Exception:
                print("Unable to build knowledge graph from file.")
                print("Please use .ingest() method with your data first")

        response = self.chain.invoke(query_str)

        return response

    def _graph_builder(self, triples: List[Tuple[str]]):
        graph = NetworkxEntityGraph()
        for triple in triples:
            triple = KnowledgeTriple(triple[0], triple[1], triple[2])
            graph.add_triple(triple)
        if self.safe_graph:
            graph.write_to_gml(self.graph_name)
        return graph

    def _remove_sections(text, blacklist):
        """Removes entire sections based on header names"""
        # Split text into sections using header markers
        sections = re.split(r"(?m)^(==+)\s*(.*?)\s*\1\s*$", text)
        if len(sections) < 2:
            return text

        # Process sections: [lead, header_marker, header, header_marker, content, ...]
        cleaned_sections = []
        # current_header = None

        # Always keep the lead section (content before first header)
        cleaned_sections.append(sections[0])

        # Process subsequent sections
        for i in range(1, len(sections), 3):
            if i + 2 >= len(sections):
                break

            header_marker = sections[i]
            header = sections[i + 1]
            content = sections[i + 2]

            # Normalize header for comparison
            normalized_header = header.strip().lower()

            # Keep section if not in blacklist
            if normalized_header not in blacklist:
                cleaned_sections.append(header_marker)
                cleaned_sections.append(header)
                cleaned_sections.append(header_marker)
                cleaned_sections.append(content)

        return "".join(cleaned_sections)

    def _clean_page(self, uncleaned: dict, section_blacklist: list = None):
        clean_content = {}
        if section_blacklist is None:
            section_blacklist = [
                "gallery",
                "soundtrack",
                "videos",
                "references",
                "title updates",
                "appearances",
                "other media",
            ]
        for page, content in uncleaned.items():
            # Convert to lowercase for case-insensitive matching
            section_blacklist = [s.lower() for s in section_blacklist]
            # cleaned = enhanced_clean_wiki_text(content)
            cleaned = self._remove_sections(content, section_blacklist)
            # Remove references and URLs
            cleaned = re.sub(r"\[\d+\]", "", cleaned)  # [1], [2] style references
            cleaned = re.sub(
                r"\[https?://[^\s]+\s+([^\]]+)\]", r"\1", cleaned
            )  # [http://... Label]
            cleaned = re.sub(r"https?://\S+", "", cleaned)  # Bare URLs

            # Remove all {{templates}} including multi-line templates
            # cleaned = re.sub(r'\{\{.*?\}\}', '', cleaned, flags=re.DOTALL)
            # cleaned = clean_wiki_text(content)
            clean_content[page] = cleaned
        return clean_content

    def _get_triples(self, text) -> List[Tuple[str, str, str]]:
        """Function to extract knowledge triples from a given text
        then add the triples to the main list
        """
        # create a temporary temporary graph and extract the triples.
        graph = self.index_creator.from_text(text)
        triples = graph.get_triples()

        return triples

    def __estimate_token_count(self, input_string):
        # Tokenize the string into words and punctuation using regex
        tokens = self.text_splitter.split_text(input_string)
        # tokens = re.findall(r'\b\w+\b|[^\w\s]', input_string)
        return len(tokens)


if __name__ == "__main__":
    with open("wiki_content.json", "r") as f:
        dirty_data = json.load(f)

    builder = graph_builder()
    builder.ingest(dirty_data)
    builder.query("How is Alani Kelso?")
