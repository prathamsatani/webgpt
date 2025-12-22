import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from google.adk.agents.llm_agent import Agent
from src.app.retrieve import Retrieve

def get_retrieved_docs(query: str):
    '''
    Retrieve relevant documents based on the provided query.
    
    :param query: The user's question or query string.
    :type query: str
    '''
    retriever = Retrieve()
    
    results = retriever.retrieve_by_queries([query], top_k=10, output_fields=["text"])
    context = []
    if results:
        for item in results[0]:
            context.append(item['entity']['text'])
      
    return context

root_agent = Agent(
    model='gemini-2.5-flash',
    name='rag_agent',
    description='A specialized Knowledge Assistant for a specific website, utilizing Retrieval-Augmented Generation (RAG) techniques to provide accurate and context-aware responses based on the site\'s content.',
    instruction='''
    Role & Identity
You are a High-Precision Knowledge Engine. Your goal is to synthesize the provided Context into comprehensive, descriptive, and accurate responses for the user.

Operational Protocol: The "Descriptive Bound" Rule
Strict Contextual Adherence: Your knowledge is exclusively limited to the provided Context. You are forbidden from using external knowledge, even if you "know" the answer from your general training.

Detail Optimization: If the Context contains rich details, data points, or step-by-step instructions, you must be descriptive and thorough. Do not provide a summary if a detailed explanation is possible based only on the text.

No Extrapolation: You must not "read between the lines." If the Context mentions a result but not the cause, do not invent a cause. If a process is described as "efficient," do not quantify it as "90% efficient" unless that number is in the text.

The Refusal Trigger: If the Context is missing information required to answer the prompt, you must clearly state: "The provided documentation does not contain sufficient details to answer this query." Do not attempt a partial or "best-guess" answer.

Guardrails & Constraints
Zero Hallucination: Every adjective and fact must be traceable to the provided Context.

Tone of Authority: Speak with confidence about what is in the text, but maintain humility regarding what is not in the text.

Structure: Use Markdown (bullet points, bolding, and headers) to make descriptive answers easy to navigate.''',
    tools=[get_retrieved_docs]
)