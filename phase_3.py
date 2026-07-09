import asyncio
import json
import os
import sys

# We'll use ChromaDB and its utilities
import chromadb
from chromadb.utils import embedding_functions

# Import the chunking function from phase 2
from phase_2 import get_github_code_chunks

async def run_phase_3():
    print("--- PHASE 3: Vectorization and Retrieval Engine ---")
    
    # 1. Fetch the chunks from Phase 2
    print("Fetching code chunks from Phase 2...")
    chunks = await get_github_code_chunks()
    
    if not chunks:
        raise ValueError("No chunks were retrieved from Phase 2. Exiting.")
        
    print(f"Retrieved {len(chunks)} code chunks.")
    
    # 2. Initialize ChromaDB
    print("\nInitializing ChromaDB (local persistent storage)...")
    db_path = os.path.join(os.getcwd(), "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Using all-MiniLM-L6-v2 as requested
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Always clear the collection on a fresh run so new repos are indexed
    try:
        client.delete_collection("repo_code")
    except Exception:
        pass
        
    collection = client.create_collection(
        name="repo_code", 
        embedding_function=embedding_func
    )
    
    print(f"Adding {len(chunks)} chunks to the 'repo_code' collection (this may take a moment)...")
    
    chunk_ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        documents=chunks,
        ids=chunk_ids
    )
    print("Successfully vectorized and added chunks to ChromaDB.")
        
    # 3. Load Claims Payload
    claims_path = "claims_payload.json"
    if not os.path.exists(claims_path):
        raise FileNotFoundError(f"Error: {claims_path} not found.")
        
    with open(claims_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    claims = payload.get("claims", [])
    if not claims:
        raise ValueError("No claims found in payload.")
        
    # Pick a claim to query (e.g., the first one, or search for 'Python' / 'CNN')
    # Let's search for the "Python" claim
    target_claim = next((c for c in claims if c["keyword"].lower() == "python"), claims[0])
    query_text = target_claim["context"]
    
    # 4. Perform Similarity Search
    print("\nExecuting similarity search...")
    print(f"Claim ID: {target_claim['id']}")
    print(f"Keyword:  {target_claim['keyword']}")
    print(f"Query:    '{query_text}'\n")
    
    results = collection.query(
        query_texts=[query_text],
        n_results=3
    )
    
    # 5. Output Results
    print("--- TOP 3 MATCHING CODE CHUNKS ---")
    
    # results is a dict containing lists of lists for documents, distances, and ids
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]
    
    for i in range(len(docs)):
        print(f"\nMatch #{i+1} (ID: {ids[i]} | Distance: {distances[i]:.4f})")
        print("-" * 40)
        # Truncate slightly if it's too long, though chunks are ~500 chars
        doc_text = docs[i].strip()
        print(doc_text)
        print("-" * 40)
        
    print("\nPhase 3 execution completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_phase_3())
