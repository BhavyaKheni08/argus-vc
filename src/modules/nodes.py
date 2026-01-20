import json
import os
from typing import TypedDict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables if they aren't already loaded
if not os.getenv("GOOGLE_API_KEY"):
    load_dotenv()

from src.modules.prompts import (
    ROUTER_SYSTEM_PROMPT, ROUTER_TASK_PROMPT,
    SHERLOCK_SYSTEM_PROMPT, SHERLOCK_TASK_PROMPT,
    RESEARCHER_SYSTEM_PROMPT, RESEARCHER_TASK_PROMPT,
    CFO_SYSTEM_PROMPT, CFO_TASK_PROMPT,
    CRITIC_SYSTEM_PROMPT, CRITIC_TASK_PROMPT,
    WRITER_SYSTEM_PROMPT, WRITER_TASK_PROMPT
)
from src.modules.tools import perform_live_search

# Initialization Helper
def get_llm():
    """Returns an initialized ChatGoogleGenerativeAI instance."""
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

# 2. State Definition
class AgentState(TypedDict):
    pdf_file_uri: str
    job_order: dict
    sherlock_report: str
    researcher_report: str
    cfo_report: str
    critic_feedback: str
    final_memo: str

# Helper to clean JSON
def extract_text_from_response(response) -> str:
    """Helper to extract text from Gemini 3 response which might be a list."""
    if isinstance(response.content, str):
        return response.content
    elif isinstance(response.content, list):
        parts = []
        for part in response.content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return "".join(parts)
    return str(response.content)

def clean_json_text(text: str) -> str:
    """Removes markdown code blocks if present."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text: # Fallback if just backticks
        text = text.split("```")[1].split("```")[0]
    return text.strip()

# 3. Node Functions

def router_node(state: AgentState) -> dict:
    """Extracts entities from the PDF into JSON."""
    pdf_uri = state["pdf_file_uri"]
    llm = get_llm()
    
    # Construct the message payload with the PDF file
    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=[
            {"type": "text", "text": ROUTER_TASK_PROMPT},
            {"type": "media", "file_uri": pdf_uri, "mime_type": "application/pdf"}
        ])
    ]
    
    response = llm.invoke(messages)
    
    try:
        content = extract_text_from_response(response)
        clean_text = clean_json_text(content)
        job_order = json.loads(clean_text)
    except json.JSONDecodeError:
        # Fallback empty structure if parsing fails
        job_order = {
            "founders": [], 
            "competitors": [], 
            "financial_claims": [], 
            "industry": "Unknown"
        }
        print("Error parsing JSON from Router Node.")

    return {"job_order": job_order}


def sherlock_node(state: AgentState) -> dict:
    """Performs background checks on founders."""
    job_order = state.get("job_order", {})
    founders = job_order.get("founders", [])
    llm = get_llm()
    
    search_results = ""
    for founder in founders:
        query = f"{founder} fraud lawsuit startup exit"
        result = perform_live_search(query)
        search_results += f"\n--- Search for {founder} ---\n{result}\n"
    
    task_prompt = SHERLOCK_TASK_PROMPT.format(
        founders=", ".join(founders),
        search_results=search_results
    )
    
    messages = [
        SystemMessage(content=SHERLOCK_SYSTEM_PROMPT),
        HumanMessage(content=task_prompt)
    ]
    
    response = llm.invoke(messages)
    return {"sherlock_report": extract_text_from_response(response)}


def researcher_node(state: AgentState) -> dict:
    """Analyzes market and competitors."""
    job_order = state.get("job_order", {})
    competitors = job_order.get("competitors", [])
    llm = get_llm()
    
    search_results = ""
    for competitor in competitors:
        # Topic='news' for competitor analysis
        result = perform_live_search(competitor, topic="news")
        search_results += f"\n--- Search for {competitor} ---\n{result}\n"
        
    task_prompt = RESEARCHER_TASK_PROMPT.format(
        competitors=", ".join(competitors),
        search_results=search_results
    )
    
    messages = [
        SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
        HumanMessage(content=task_prompt)
    ]
    
    response = llm.invoke(messages)
    return {"researcher_report": extract_text_from_response(response)}


def cfo_node(state: AgentState) -> dict:
    """Sanity checks financial claims."""
    job_order = state.get("job_order", {})
    financial_claims = job_order.get("financial_claims", [])
    llm = get_llm()
    
    # If list is empty, handle gracefully
    claims_text = "\n".join(str(c) for c in financial_claims) if financial_claims else "None provided."
    
    task_prompt = CFO_TASK_PROMPT.format(
        financial_claims=claims_text
    )
    
    messages = [
        SystemMessage(content=CFO_SYSTEM_PROMPT),
        HumanMessage(content=task_prompt)
    ]
    
    response = llm.invoke(messages)
    return {"cfo_report": extract_text_from_response(response)}


def critic_node(state: AgentState) -> dict:
    """Validates reports against the original PDF."""
    pdf_uri = state["pdf_file_uri"]
    llm = get_llm()
    
    task_prompt = CRITIC_TASK_PROMPT.format(
        sherlock_report=state.get("sherlock_report", "No report"),
        researcher_report=state.get("researcher_report", "No report"),
        cfo_report=state.get("cfo_report", "No report")
    )
    
    # Critic needs to see the PDF to validate hallucinations
    messages = [
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(content=[
            {"type": "text", "text": task_prompt},
            {"type": "media", "file_uri": pdf_uri, "mime_type": "application/pdf"}
        ])
    ]
    
    response = llm.invoke(messages)
    return {"critic_feedback": extract_text_from_response(response)}


def writer_node(state: AgentState) -> dict:
    """Compiles the final investment memo."""
    llm = get_llm()
    # Concatenate all validated data for the writer
    
    context_data = f"""
    --- Sherlock Report ---
    {state.get('sherlock_report')}
    
    --- Researcher Report ---
    {state.get('researcher_report')}
    
    --- CFO Report ---
    {state.get('cfo_report')}
    
    --- CRITIC FEEDBACK (VALIDATION) ---
    {state.get('critic_feedback')}
    """
    
    full_prompt = f"{WRITER_TASK_PROMPT}\n\nHere is the validated data:\n{context_data}"

    messages = [
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=full_prompt)
    ]
    
    response = llm.invoke(messages)
    return {"final_memo": extract_text_from_response(response)}

