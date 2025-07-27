from langchain_core.output_parsers import StrOutputParser
from typing import List

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field


# Output parser will split the LLM result into a list of queries
class LineListOutputParser(BaseOutputParser[List[str]]):
    """Output parser for a list of lines."""

    def parse(self, text: str) -> List[str]:
        lines = text.strip().split("\n")
        return list(filter(None, lines))  # Remove empty lines

output_parser = LineListOutputParser()

DECOMPOSITION_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are a helpful assistant that generates multiple sub-questions related to an input question. \n
    The goal is to break down the input into a set of sub-problems / sub-questions that can be answers in isolation. \n
    Generate multiple search queries related to: 
    Original question: {question} \n
    Output (3 queries):"""
    )

QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an AI language model assistant. Your task is to generate five 
    different versions of the given user question to retrieve relevant documents from a knowledge. 
    By generating multiple perspectives on the user question, your goal is to help
    the user overcome some of the limitations of entitites being the same bout names different. 
    Such as 'Alani Kelso' refered on some nodes as 'Alani' or 'Kelso' 
    or 'The international Manning Zoo' being refered as 'Manning Zoo' in some nodes.
    Provide these alternative questions separated by newlines.
    Original question: {question}""",
)
llm = OllamaLLM(model="qwen3:14b",temperature=0,seed=42420,reasoning=False)

# Chain
llm_chain = QUERY_PROMPT | llm | output_parser

# Other inputs
question = "Who is Alani Kelso? What is her current objective?"
response = llm_chain.invoke({"question":question})
print(response)
for question in response:
    generate_queries_decomposition = ( DECOMPOSITION_PROMPT | llm | StrOutputParser() | (lambda x: x.split("\n")))
    questions = generate_queries_decomposition.invoke({"question":question})
    print(questions)

# generate_queries_decomposition = ( prompt_decomposition | llm | StrOutputParser() | (lambda x: x.split("\n")))
# questions = generate_queries_decomposition.invoke({"question":question})