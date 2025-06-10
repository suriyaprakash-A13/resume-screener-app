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

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
RESUME_FOLDER = PROJECT_ROOT / "data" / "resumes"
JD_FOLDER = PROJECT_ROOT / "data" / "job_descriptions"
FINAL_OUTPUT = PROJECT_ROOT / "data" / "final_recommendations.json"

st.set_page_config(page_title="AI Resume Screener", layout="centered")
st.title("💼 AI Resume Screener & Recommender")
st.markdown("Upload resumes and paste a job description to get the top matched candidates.")

st.divider()

# === Upload Resumes ===
st.subheader("📤 Step 1: Upload Resumes")
resume_files = st.file_uploader(
    "Upload resumes (PDF or DOCX)", type=["pdf", "docx"], accept_multiple_files=True
)

if resume_files:
    st.success(f"✅ {len(resume_files)} resume(s) uploaded.")

# === Paste JD ===
st.subheader("📝 Step 2: Paste Job Description")
jd_text_input = st.text_area("Paste the job description below:", height=200)

st.divider()

# === Run Pipeline ===
if st.button("🚀 Run Screening Pipeline"):
    if not resume_files or not jd_text_input.strip():
        st.warning("⚠️ Please upload resumes and paste a job description.")
    else:
        # Clean folders
        shutil.rmtree(RESUME_FOLDER, ignore_errors=True)
        shutil.rmtree(JD_FOLDER, ignore_errors=True)
        RESUME_FOLDER.mkdir(parents=True, exist_ok=True)
        JD_FOLDER.mkdir(parents=True, exist_ok=True)

        # Save resumes
        for resume in resume_files:
            with open(RESUME_FOLDER / resume.name, "wb") as f:
                f.write(resume.read())

        # Save JD
        with open(JD_FOLDER / "job_description.txt", "w", encoding="utf-8") as f:
            f.write(jd_text_input.strip())

        # Run pipeline
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

        # Load output
        if FINAL_OUTPUT.exists():
            with open(FINAL_OUTPUT, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)

            # Extract name from text
            def extract_name_from_text(raw_text, fallback):
                lines = raw_text.strip().split("\n")[:5]
                common_headings = {"Professional Summary", "Objective", "Experience", "Skills", "Education"}
                for line in lines:
                    line = line.strip()
                    if line in common_headings:
                        continue
                    if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", line):
                        return line
                return fallback

            df["Candidate"] = df.apply(
                lambda row: extract_name_from_text(row.get("raw", ""), row.get("file_name")),
                axis=1
            )

            # Final display table
            display_df = df[[
                "Candidate", "email", "phone", "skills", "match_score",
                "soft_skills", "red_flags", "recommendation_score", "file_name"
            ]].rename(columns={
                "email": "Email",
                "phone": "Phone",
                "skills": "Skills",
                "match_score": "Match %",
                "soft_skills": "Soft Skills",
                "red_flags": "Red Flags",
                "recommendation_score": "Final Score",
                "file_name": "Resume File"
            })

            st.success("🏆 Top 5 Recommended Candidates")

            # Display candidate cards
            for _, row in display_df.iterrows():
                with st.expander(f"👤 {row['Candidate']} - Score: {row['Final Score']}"):
                    st.write(f"📧 **Email**: {row['Email']}")
                    st.write(f"📞 **Phone**: {row['Phone']}")
                    st.write(f"🧠 **Skills**: {', '.join(row['Skills'])}")
                    st.write(f"💬 **Soft Skills**: {', '.join(row['Soft Skills'])}")
                    red_flags = ', '.join(row['Red Flags']) or "None"
                    st.write(f"⚠️ **Red Flags**: {red_flags}")

                    # Download resume
                    resume_path = RESUME_FOLDER / row["Resume File"]
                    if resume_path.exists():
                        with open(resume_path, "rb") as f:
                            base64_resume = base64.b64encode(f.read()).decode()
                        href = f'<a href="data:application/octet-stream;base64,{base64_resume}" download="{row["Resume File"]}">📎 Download Resume</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.warning("Resume file not found.")

            # CSV download
            csv_data = display_df.drop(columns=["Resume File"]).to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download as CSV", csv_data, "top_5_candidates.csv", "text/csv")

            # PDF generation
            def create_pdf(dataframe):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Top 5 Resume Recommendations", ln=True, align='C')
                pdf.ln(10)

                for _, row in dataframe.iterrows():
                    pdf.set_font("Arial", "B", size=12)
                    pdf.cell(200, 10, txt=f"{row['Candidate']} - Score: {row['Final Score']}", ln=True)
                    pdf.set_font("Arial", size=11)
                    pdf.cell(200, 8, txt=f"Email: {row['Email']}", ln=True)
                    pdf.cell(200, 8, txt=f"Phone: {row['Phone']}", ln=True)
                    pdf.cell(200, 8, txt=f"Skills: {', '.join(row['Skills'])}", ln=True)
                    pdf.cell(200, 8, txt=f"Soft Skills: {', '.join(row['Soft Skills'])}", ln=True)
                    red_flags = ", ".join(row['Red Flags']) or "None"
                    pdf.cell(200, 8, txt=f"Red Flags: {red_flags}", ln=True)
                    pdf.ln(5)

                pdf_path = PROJECT_ROOT / "data" / "top_5_candidates.pdf"
                pdf.output(str(pdf_path))
                return pdf_path

            pdf_path = create_pdf(display_df)
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download as PDF", f.read(), "top_5_candidates.pdf", "application/pdf")

        else:
            st.error("❌ No output file found.")
