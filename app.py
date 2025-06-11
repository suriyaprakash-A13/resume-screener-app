import streamlit as st
from pathlib import Path
import shutil
import json
import pandas as pd
import re
from fpdf import FPDF
import base64

from utils.resume_parser import batch_parse_resumes
from agents.recruiter_agent import batch_process_recruiter
from agents.analyst_agent import batch_process_analyst
from agents.hr_agent import batch_process_hr
from agents.recommender_agent import batch_process_recommender

# Set page config FIRST
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# Custom dark theme styling
st.markdown("""
    <style>
    body {
        background-color: #111827;
        color: white;
    }
    .stApp {
        background-color: #111827;
    }
    .stButton>button {
        color: white;
        background: #4F46E5;
        border-radius: 5px;
    }
    .stTextInput>div>div>input, .stTextArea textarea {
        background-color: #1f2937;
        color: white;
    }
    .stDownloadButton>button {
        background-color: #10B981;
        color: white;
    }
    .css-1d391kg p {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
RESUME_FOLDER = PROJECT_ROOT / "data" / "resumes"
JD_FOLDER = PROJECT_ROOT / "data" / "job_descriptions"
FINAL_OUTPUT = PROJECT_ROOT / "data" / "final_recommendations.json"

st.title("AI Resume Screener & Recommender")
st.markdown("Upload resumes and paste a job description to get the top matched candidates.")
st.divider()

# Upload resumes
st.subheader("Upload Resumes")
resume_files = st.file_uploader("Upload resumes (PDF or DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

if resume_files:
    st.success(f"✅ {len(resume_files)} resume(s) uploaded.")

# Paste JD
st.subheader("Paste Job Description")
jd_text_input = st.text_area("Paste the job description below:", height=200)

st.divider()

# Run Screening Pipeline
if st.button("Run Screening Pipeline"):
    if not resume_files or not jd_text_input.strip():
        st.warning("⚠️ Please upload resumes and paste a job description.")
    else:
        shutil.rmtree(RESUME_FOLDER, ignore_errors=True)
        shutil.rmtree(JD_FOLDER, ignore_errors=True)
        RESUME_FOLDER.mkdir(parents=True, exist_ok=True)
        JD_FOLDER.mkdir(parents=True, exist_ok=True)

        for resume in resume_files:
            with open(RESUME_FOLDER / resume.name, "wb") as f:
                f.write(resume.read())

        with open(JD_FOLDER / "job_description.txt", "w", encoding="utf-8") as f:
            f.write(jd_text_input.strip())

        # Run each agent
        with st.spinner("🔍 Parsing resumes..."):
            batch_parse_resumes()
        with st.spinner("📧 Extracting contact info..."):
            batch_process_recruiter()
        with st.spinner("📊 Matching resumes to job description..."):
            batch_process_analyst()
        with st.spinner("💬 Analyzing soft skills and red flags..."):
            batch_process_hr()
        with st.spinner("🎯 Ranking top candidates..."):
            batch_process_recommender()

        # Display results
        if FINAL_OUTPUT.exists():
            with open(FINAL_OUTPUT, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)

            def extract_name_from_text(raw_text, fallback):
                lines = raw_text.strip().split("\n")[:5]
                common_headings = {"Professional Summary", "Objective", "Experience", "Skills", "Education"}
                for line in lines:
                    if line.strip() in common_headings:
                        continue
                    if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", line.strip()):
                        return line.strip()
                return fallback

            df["Candidate"] = df.apply(
                lambda row: extract_name_from_text(row.get("raw", ""), row.get("file_name")),
                axis=1
            )

            # Display top candidates
            st.success("Top 5 Recommended Candidates")
            top_5 = df.sort_values(by="recommendation_score", ascending=False).head(5)

            for _, row in top_5.iterrows():
                with st.expander(f"🧑 {row['Candidate']} - Final Score: {round(row['recommendation_score'], 2)}"):
                    st.markdown(f"""
                        <div style='background-color:#1e293b; padding: 10px; border-radius: 10px;'>
                        <b style='color:#60a5fa;'>Recruiter:</b> {round(row.get("recruiter_score", 0), 2)}<br>
                        <b style='color:#818cf8;'>Analyst:</b> {round(row.get("analyst_score", 0), 2)}<br>
                        <b style='color:#f472b6;'>HR:</b> {round(row.get("hr_score", 0), 2)}<br>
                        <b style='color:#10b981;'>Total:</b> {round(row['recommendation_score'], 2)}
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"📧 **Email:** `{row['email']}`")
                    st.markdown(f"📞 **Phone:** `{row['phone']}`")
                    st.markdown(f"🧠 **Skills:** {', '.join(row.get('skills', []))}")
                    st.markdown(f"💬 **Soft Skills:** {', '.join(row.get('soft_skills', [])) or 'None'}")
                    st.markdown(f"⚠️ **Red Flags:** {', '.join(row.get('red_flags', [])) or 'None'}")
                    st.markdown(f"📝 **Feedback:** {row.get('feedback', 'No feedback generated.')}")

                    resume_path = RESUME_FOLDER / row["file_name"]
                    if resume_path.exists():
                        with open(resume_path, "rb") as f:
                            resume_data = base64.b64encode(f.read()).decode()
                            href = f'<a href="data:application/octet-stream;base64,{resume_data}" download="{row["file_name"]}">📎 Download Resume</a>'
                            st.markdown(href, unsafe_allow_html=True)

            # CSV Download
            csv = top_5.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "top_candidates.csv", "text/csv")

        else:
            st.error("❌ No output file found.")
