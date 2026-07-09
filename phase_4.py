import json
import os
import sys

import chromadb
from chromadb.utils import embedding_functions

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import JsonOutputParser

def mock_llm_call(prompt_val):
    import re
    # Extract the actual string value from the LangChain prompt object
    prompt_str = prompt_val.to_string()
    
    # Safely extract the claim being evaluated to prevent overlap with code evidence
    claim_match = re.search(r"Claim:\s*(.*?)\n", prompt_str)
    claim_text = claim_match.group(1).lower() if claim_match else ""
    
    # Extract unique repository names from the code evidence headers only
    repos = set(re.findall(r"^---\s*Repository:\s*([^|\s]+)\s*\|", prompt_str, re.MULTILINE))
    repo_context = f"repositories ({', '.join(repos)})" if repos else "repository"
    
    # If there is no code evidence at all (i.e., no repos were scanned)
    if not repos:
        return json.dumps({
            "verdict": "Hallucinated",
            "reasoning": f"No code repositories could be successfully scanned to verify '{claim_text}'."
        })

    # Advanced Mock Logic: Actually scan the code evidence for keywords/syntax related to the claim!
    code_evidence_lower = prompt_str.lower()
    
    # Define common tech synonyms/indicators in code
    tech_indicators = {
        "python": [".py", "def ", "import ", "print("],
        "react": ["react", ".jsx", ".tsx", "useeffect", "usestate", "export default function", "npm"],
        "java": [".java", "public class ", "system.out", "public static void"],
        "sql": [".sql", "select ", "insert into", "create table", "query"],
        "tensorflow": ["tensorflow", "tf.", "keras", "sequential"],
        "cnn": ["conv2d", "maxpooling", "keras", "tensorflow"],
        "convolutional": ["conv2d", "maxpooling", "keras", "tensorflow"],
        "machine learning": ["sklearn", "model.fit", "predict", "import pandas", "import numpy"]
    }
    
    # If we don't have hardcoded indicators, just look for the claim text itself
    indicators = tech_indicators.get(claim_text, [claim_text])
    
    # Check if ANY of the indicators exist in the code evidence
    found = any(ind in code_evidence_lower for ind in indicators)
    
    if found:
        verdict = "Verified"
        reasoning = f"Code chunks from the candidate's {repo_context} contain explicit syntax or library imports confirming {claim_text} expertise."
    else:
        verdict = "Hallucinated"
        reasoning = f"After scanning the candidate's {repo_context}, no evidence, syntax, or library usage for '{claim_text}' was found in the codebase."
        
    response = {
        "verdict": verdict,
        "reasoning": reasoning
    }
    # Return it as a JSON string to simulate an LLM's raw output before parsing
    return json.dumps(response)

def run_phase_4():
    print("--- PHASE 4: The Judge Agent ---")
    
    # 1. Load Claims Payload
    claims_path = "claims_payload.json"
    if not os.path.exists(claims_path):
        raise FileNotFoundError(f"Error: {claims_path} not found.")
        
    with open(claims_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    claims = payload.get("claims", [])
    if not claims:
        raise ValueError("No claims found to evaluate.")
        
    # 2. Connect to ChromaDB
    print("Connecting to ChromaDB 'repo_code' collection...")
    db_path = os.path.join(os.getcwd(), "chroma_db")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Error: ChromaDB directory '{db_path}' not found.")
        
    client = chromadb.PersistentClient(path=db_path)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    try:
        collection = client.get_collection(name="repo_code", embedding_function=embedding_func)
    except Exception as e:
        raise RuntimeError(f"Error retrieving collection: {e}")
        
    # 3. Setup LangChain Prompt and Chain
    # The prompt instructs the LLM to act as a senior technical interviewer
    template = """You are a strict, senior technical interviewer. Your task is to evaluate the validity of a candidate's resume claim based ONLY on the provided code evidence.

Claim: {claim}

Code Evidence:
{code_evidence}

Evaluate if the code supports the claim. You must respond in a structured JSON format containing exactly two fields:
1. "verdict": Must be exactly one of: "Verified", "Partial", or "Hallucinated"
2. "reasoning": A 1-2 sentence explanation of why the code does or does not support the claim.
"""
    prompt = PromptTemplate.from_template(template)
    
    # Normally we would use something like ChatOpenAI(temperature=0), 
    # but we use a mock for the demo to run end-to-end without an API key
    # llm = ChatOpenAI(model="gpt-4o", temperature=0)
    mock_llm = RunnableLambda(mock_llm_call)
    
    # JSON output parser ensures we get a Python dict from the LLM's JSON string
    parser = JsonOutputParser()
    
    # Combine everything into a pipeline
    chain = prompt | mock_llm | parser
    
    # 4. Evaluate Each Claim
    print("\nEvaluating claims...\n")
    audit_results = []
    
    for claim in claims:
        claim_context = claim["context"]
        print(f"Analyzing claim: {claim['keyword']}...")
        
        # Retrieve top 10 chunks (chunks are now larger)
        results = collection.query(
            query_texts=[claim_context],
            n_results=10
        )
        
        docs = results.get("documents", [[]])[0]
        code_evidence = "\n\n---\n\n".join(docs)
        
        # Invoke the chain
        try:
            evaluation = chain.invoke({
                "claim": claim_context,
                "code_evidence": code_evidence
            })
            
            # Append verdict and reasoning to the original claim
            claim["verdict"] = evaluation.get("verdict", "Unknown")
            claim["reasoning"] = evaluation.get("reasoning", "No reasoning provided.")
            audit_results.append(claim)
            
            print(f" -> Verdict: {claim['verdict']}")
        except Exception as e:
            print(f" -> Error during evaluation: {e}", file=sys.stderr)
            claim["verdict"] = "Error"
            claim["reasoning"] = str(e)
            audit_results.append(claim)
            
    # 5. Save Final Audit Report
    report_data = {"audit_report": audit_results}
    report_path = "final_audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
        
    print(f"\n--- PHASE 4 SUCCESS ---")
    print(f"Final audit report saved to {report_path}")
    print("\nPreview of the Final Audit Report:")
    print(json.dumps(report_data, indent=2))
    
    print("\nNote: The LLM step is currently mocked for end-to-end verification.")
    print("To use a real model, replace `mock_llm` with your initialized LLM (e.g., `ChatOpenAI(api_key='YOUR_API_KEY')`).")

if __name__ == "__main__":
    run_phase_4()
