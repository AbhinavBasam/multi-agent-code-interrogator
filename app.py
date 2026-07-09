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
    github_url = st.text_input("GitHub Repository URL", "https://github.com/encode/starlette")
    
    if st.button("Run Audit Pipeline", type="primary"):
        st.info("In a live deployment, this would trigger Phases 1-4 pipeline asynchronously. For now, we are displaying the most recent local audit.")

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
