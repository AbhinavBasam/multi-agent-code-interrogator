# -*- coding: utf-8 -*-
import streamlit as st
import json
import os
import sys

# Ensure stdout uses UTF-8 to prevent charmap errors on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Configure the main page layout
st.set_page_config(page_title="Multi-Agent Code Interrogator", page_icon="🕵️‍♂️", layout="wide")

# App Header & Description
st.title("🕵️‍♂️ Multi-Agent Code Interrogator")
st.markdown("""
Welcome to the Multi-Agent Code Interrogator. This system evaluates a candidate's resume claims by deeply cross-referencing them with their actual GitHub codebase. 
It utilizes a multi-agent architecture to extract claims, ingest repository code into a vector database, and perform semantic verification via LLMs.
""")

# Sidebar for simulating the initial ingestion phase
with st.sidebar:
    st.header("Ingestion Configuration")
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    github_url = st.text_input("GitHub Repository URL (Optional, will read from resume if blank)", "")
    
    if st.button("Run Audit Pipeline", type="primary"):
        if not uploaded_file:
            st.warning("Please upload a resume first.")
        else:
            with st.spinner("Running Audit Pipeline... This may take a few minutes."):
                # Save the uploaded file
                with open("resume.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                username = None
                import re
                import fitz
                
                # 1. Try from input URL
                if github_url.strip():
                    match = re.search(r"github\.com/([^/\s]+)", github_url)
                    if match:
                        username = match.group(1)
                
                # 2. Try from PDF
                if not username:
                    try:
                        doc = fitz.open("resume.pdf")
                        full_text = ""
                        for page in doc:
                            full_text += page.get_text("text") + "\n"
                        match = re.search(r"github\.com/([^/\s]+)", full_text, re.IGNORECASE)
                        if match:
                            username = match.group(1)
                    except Exception as e:
                        pass
                
                if not username:
                    st.error("Could not find a GitHub URL in the provided input or the resume PDF.")
                    st.stop()
                    
                # Save to github_config.json
                with open("github_config.json", "w") as f:
                    json.dump({"github_username": username}, f)
                
                # Run the pipeline
                import subprocess
                try:
                    subprocess.run([sys.executable, "phase_1.py", "resume.pdf"], check=True)
                    subprocess.run([sys.executable, "phase_1_part2.py", "resume.pdf"], check=True)
                    subprocess.run([sys.executable, "phase_2.py"], check=True)
                    subprocess.run([sys.executable, "phase_3.py"], check=True)
                    subprocess.run([sys.executable, "phase_4.py"], check=True)
                    st.success("Pipeline completed successfully!")
                except subprocess.CalledProcessError as e:
                    st.error(f"Pipeline failed at a step. Check your terminal logs.")

st.divider()
st.header("Final Audit Report")

# Load data generated from Phase 4
report_path = "final_audit_report.json"
if os.path.exists(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            audit_report = data.get("audit_report", [])
            
            # Display high-level candidate info
            st.subheader("Candidate Overview")
            col1, col2 = st.columns(2)
            col1.metric("Candidate Name", "Abhinav Basam")  
            col2.metric("Target Role", "AI & ML Engineer")
            
            st.subheader("Skill Verification Results")
            
            if not audit_report:
                st.warning("No claims found in the audit report.")
            else:
                for claim in audit_report:
                    keyword = claim.get("keyword", "Unknown")
                    verdict = claim.get("verdict", "Unknown")
                    context = claim.get("context", "No context provided.")
                    reasoning = claim.get("reasoning", "No reasoning provided.")
                    
                    # Using unicode escapes instead of raw emojis to prevent any Windows encoding errors
                    if verdict == "Verified":
                        emoji = "\u2705"  # Check mark
                        color = "green"
                    elif verdict == "Partial":
                        emoji = "\u26A0\uFE0F"  # Warning sign
                        color = "orange"
                    else:
                        emoji = "\u274C"  # Cross mark
                        color = "red"
                        
                    # Build expander for each claim
                    with st.expander(f"{emoji} **{keyword}** - {verdict}"):
                        st.markdown(f"**Claim Context:** {context}")
                        st.markdown(f"**Verdict:** :{color}[**{verdict}**]")
                        st.markdown(f"**Reasoning:** {reasoning}")
                        
        except json.JSONDecodeError:
            st.error("Error reading the final audit report JSON. Ensure it is formatted correctly.")
else:
    st.error(f"Audit report not found at `{report_path}`. Please run Phase 4 first to generate the report.")
