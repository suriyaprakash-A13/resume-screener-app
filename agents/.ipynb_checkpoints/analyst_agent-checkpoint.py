import sys
from pathlib import Path
import json
from sentence_transformers import SentenceTransformer, util

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ✅ Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "recruiter_enriched.json"
JD_FILE = PROJECT_ROOT / "data" / "job_descriptions" / "job_description.txt"
OUTPUT_FILE = PROJECT_ROOT / "data" / "analyst_output.json"

# 🧠 Load the transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🧮 Compare resume with JD using cosine similarity
def compute_analyst_score(resume_text, jd_text):
    resume_embed = model.encode(resume_text, convert_to_tensor=True)
    jd_embed = model.encode(jd_text, convert_to_tensor=True)
    similarity = util.cos_sim(resume_embed, jd_embed).item()
    return round(similarity * 100, 2)  # score out of 100

# 💬 Feedback based on match
def analyst_feedback(score):
    if score > 75:
        return "Excellent alignment with job description."
    elif score > 50:
        return "Moderate alignment with job description."
    elif score > 30:
        return "Some relevant skills but also gaps."
    else:
        return "Low skill match. Consider for other roles."

# 🤖 Main agent function
def analyst_agent(resume, jd_text):
    resume_text = resume.get("clean_text", "") or resume.get("full_text", "")
    score = compute_analyst_score(resume_text, jd_text)
    feedback = analyst_feedback(score)

    resume["analyst_score"] = score
    resume["match_score"] = score  # for compatibility
    resume["analyst_feedback"] = feedback

    return resume

# 🗂️ Batch processor
def batch_process_analyst():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return
    if not JD_FILE.exists():
        print(f"❌ Job description not found: {JD_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    with open(JD_FILE, "r", encoding="utf-8") as f:
        jd_text = f.read()

    scored = [analyst_agent(resume, jd_text) for resume in resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2)

    print(f"✅ Analyst Agent scored {len(scored)} resumes and saved to {OUTPUT_FILE}")
