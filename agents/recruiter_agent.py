import sys
from pathlib import Path
import re
import json

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ✅ Imports
from utils.resume_parser import extract_text, parse_resume

# 📁 Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "recruiter_output.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "recruiter_enriched.json"

# 📧 Extract email
def extract_email(text):
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else None

# 📞 Extract phone number
def extract_phone(text):
    match = re.search(r"\+?\d[\d\s\-]{8,}\d", text)
    return match.group(0) if match else None

# 🧼 Clean resume text
def clean_resume(text):
    return ' '.join(text.split())

# 🧮 Score based on contact info
def compute_recruiter_score(email, phone):
    score = 0
    if email:
        score += 50
    if phone:
        score += 50
    return score  # Out of 100

# 💬 Feedback generator
def recruiter_feedback(score, email, phone):
    feedback = []
    if not email:
        feedback.append("Missing email.")
    if not phone:
        feedback.append("Missing phone number.")
    if score == 100:
        feedback.append("Contact info complete.")
    elif score >= 50:
        feedback.append("Partial contact info available.")
    else:
        feedback.append("No contact details found.")
    return " ".join(feedback)

# 🤖 Main agent function
def recruiter_agent(parsed_resume):
    full_text = parsed_resume.get("raw", "") or parsed_resume.get("full_text", "")
    email = extract_email(full_text)
    phone = extract_phone(full_text)
    recruiter_score = compute_recruiter_score(email, phone)
    feedback = recruiter_feedback(recruiter_score, email, phone)

    enriched = parsed_resume.copy()
    enriched.update({
        "email": email,
        "phone": phone,
        "clean_text": clean_resume(full_text),
        "recruiter_score": recruiter_score,
        "recruiter_feedback": feedback
    })
    return enriched

# 🗂️ Batch processor
def batch_process_recruiter():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        parsed_resumes = json.load(f)

    enriched_resumes = [recruiter_agent(resume) for resume in parsed_resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched_resumes, f, indent=2)

    print(f"✅ Recruiter Agent enriched {len(enriched_resumes)} resumes and saved to {OUTPUT_FILE}")
