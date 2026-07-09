import fitz  # PyMuPDF
import sys
import os

# Reconfigure stdout to handle UTF-8 properly, especially on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def clean_text(text):
    # Normalize common non-ASCII punctuation/formatting characters
    replacements = {
        "\u2014": " - ",  # em-dash
        "\u2013": "-",    # en-dash
        "\u2022": "*",    # bullet point
        "\u00a0": " ",    # non-breaking space
        "\u200b": "",     # zero-width space
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
        
    text = text.strip()
    
    # Split text into lines to process each line individually
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # Standardize spaces within each line
        cleaned_line = " ".join(line.split())
        cleaned_lines.append(cleaned_line)
        
    # Reassemble the lines and collapse multiple consecutive empty lines
    final_lines = []
    for line in cleaned_lines:
        if line == "":
            # Only add an empty line if the previous line wasn't empty
            if final_lines and final_lines[-1] != "":
                final_lines.append("")
        else:
            final_lines.append(line)
            
    return "\n".join(final_lines)

def run_phase_1(pdf_path="resume.pdf"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Error: {pdf_path} not found in the current directory.")
        
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Error opening PDF: {e}")
        
    full_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        full_text.append(text)
        
    raw_text = "\n".join(full_text)
    cleaned = clean_text(raw_text)
    
    print("--- EXTRACTED AND CLEANED TEXT ---")
    print(cleaned)
    print("----------------------------------")
    return cleaned

if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "resume.pdf"
    run_phase_1(pdf_file)
