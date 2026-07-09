import fitz
import sys
import os
import re

# Import the clean_text function from our previous script
from phase_1 import clean_text

def extract_keywords(text):
    """
    Parses the text for specific technical keywords using regex matching.
    Returns a dictionary of found keywords and their frequencies.
    """
    # Define a list of technical keywords to look for (using regex patterns if needed)
    target_keywords = [
        r'TensorFlow', 
        r'CNN', 
        r'Python', 
        r'React',
        r'Machine Learning',
        r'Deep Learning',
        r'Java',
        r'SQL',
        r'FastAPI',
        r'Flask',
        r'pandas',
        r'NumPy',
        r'scikit-learn',
        r'Keras',
        r'Docker',
        r'Git',
        r'GCP'
    ]
    
    found_keywords = {}
    for kw in target_keywords:
        # Use word boundaries \b for exact word matches, and ignore case
        # For CNN, we might want to catch CNNs as well, so we can adjust the pattern slightly
        if kw == r'CNN':
            pattern = r'\bCNNs?\b'
        else:
            pattern = rf'\b{kw}\b'
            
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Store the original keyword capitalization as the key, and the count
            found_keywords[kw] = len(matches)
            
    return found_keywords

def run_phase_1_part2(pdf_path="resume.pdf"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Error: {pdf_path} not found in the current directory.")
        
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Error opening PDF: {e}")
        
    # 1. Extract raw text
    full_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        full_text.append(text)
        
    raw_text = "\n".join(full_text)
    
    # Extract candidate name (first non-empty line)
    candidate_name = "Unknown Candidate"
    for line in raw_text.splitlines():
        if line.strip():
            candidate_name = line.strip()
            break
            
    import json
    with open("candidate_info.json", "w", encoding="utf-8") as f:
        json.dump({"candidate_name": candidate_name}, f)
    
    # 2. Clean text using the function from Phase 1
    cleaned = clean_text(raw_text)
    
    # 3. Parse for keywords
    print("--- PARSING RESUME FOR KEYWORDS ---")
    keyword_frequencies = extract_keywords(cleaned)
    
    if keyword_frequencies:
        print("Found the following technical keywords:\n")
        # Sort by frequency descending
        sorted_keywords = sorted(keyword_frequencies.items(), key=lambda item: item[1], reverse=True)
        
        claims = []
        claim_id = 1
        for kw, count in sorted_keywords:
            print(f"- {kw}: {count} occurrence(s)")
            
            # Create a claim for the top 5 keywords
            if claim_id <= 5:
                claims.append({
                    "id": f"claim_{claim_id}",
                    "keyword": kw,
                    "context": f"Candidate claims expertise in {kw} based on their resume."
                })
                claim_id += 1
                
        # Dynamically save to claims_payload.json
        with open("claims_payload.json", "w", encoding="utf-8") as f:
            json.dump({"claims": claims}, f, indent=2)
        print("\nDynamically generated claims_payload.json!")
    else:
        print("No targeted technical keywords found.")
        # Create an empty claims payload if none found
        with open("claims_payload.json", "w", encoding="utf-8") as f:
            json.dump({"claims": []}, f, indent=2)
    print("-----------------------------------")
    
    # 4. Extract GitHub Username
    github_match = re.search(r'github\.com/([A-Za-z0-9_-]+)', cleaned, re.IGNORECASE)
    if github_match:
        username = github_match.group(1)
        with open("github_config.json", "w") as f:
            json.dump({"github_username": username}, f)
        print(f"Extracted GitHub Username: {username}")
        print("Saved to github_config.json")
    else:
        print("No GitHub URL found in the resume.")

if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "resume.pdf"
    run_phase_1_part2(pdf_file)
