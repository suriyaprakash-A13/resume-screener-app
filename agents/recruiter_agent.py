import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import re
import json

# ✅ Import from resume_parser
from utils.resume_parser import extract_text, parse_resume

# 📥 Setup project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_FOLDER = PROJECT_ROOT / "data" / "resumes"
OUTPUT_FILE = PROJECT_ROOT / "data" / "recruiter_enriched.json"

# 🔍 Extract email using regex
def extract_email(text):
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else None

# 📞 Extract phone using regex
def extract_phone(text):
    match = re.search(r"\+?\d[\d\s\-]{8,}\d", text)
    return match.group(0) if match else None

# 🧹 Clean resume text
def clean_resume(text):
    return ' '.join(text.split())

# 🤖 Recruiter agent to enrich parsed data
def recruiter_agent(parsed_resume):
    full_text = parsed_resume.get("raw", "")
    enriched = parsed_resume.copy()

    enriched["email"] = extract_email(full_text)
    enriched["phone"] = extract_phone(full_text)
    enriched["clean_text"] = clean_resume(full_text)

    return enriched

# 🚀 Batch processor for all resumes
def batch_process_recruiter():
    INPUT_FILE = PROJECT_ROOT / "data" / "recruiter_output.json"

    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        parsed_resumes = json.load(f)

    enriched_resumes = [recruiter_agent(resume) for resume in parsed_resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched_resumes, f, indent=2)

    print(f"✅ Recruiter Agent enriched {len(enriched_resumes)} resumes and saved to {OUTPUT_FILE}")
