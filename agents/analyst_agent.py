import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
from sentence_transformers import SentenceTransformer, util

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "recruiter_enriched.json"
JD_FILE = PROJECT_ROOT / "data" / "job_descriptions" / "job_description.txt"
OUTPUT_FILE = PROJECT_ROOT / "data" / "analyst_output.json"

# === Load model ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Agent ===
def analyst_agent(resume: dict, jd_text: str) -> dict:
    resume_skills = resume.get("skills", [])
    if not resume_skills:
        resume["match_score"] = 0
        resume["matched_skills"] = []
        resume["missing_skills"] = []
        return resume

    jd_skills = list(set(word.lower() for word in jd_text.split() if len(word) > 2))
    
    # Embeddings
    resume_embed = model.encode(" ".join(resume_skills), convert_to_tensor=True)
    jd_embed = model.encode(" ".join(jd_skills), convert_to_tensor=True)

    similarity = util.cos_sim(resume_embed, jd_embed).item() * 100
    resume["match_score"] = round(similarity, 2)

    resume["matched_skills"] = [skill for skill in resume_skills if skill in jd_skills]
    resume["missing_skills"] = [skill for skill in jd_skills if skill not in resume_skills]

    return resume

# === Batch runner ===
def batch_process_analyst():
    if not INPUT_FILE.exists() or not JD_FILE.exists():
        print("❌ Missing input files.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    with open(JD_FILE, "r", encoding="utf-8") as f:
        jd_text = f.read()

    results = [analyst_agent(resume, jd_text) for resume in resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Analyst Agent scored {len(results)} resumes and saved to {OUTPUT_FILE}")
