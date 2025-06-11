import sys
from pathlib import Path
import json
import re

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ✅ Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "analyst_output.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "hr_output.json"

# 🔎 Define soft skills and red flag keywords
SOFT_SKILLS = {"communication", "teamwork", "leadership", "problem solving", "time management", "adaptability", "creativity", "collaboration"}
RED_FLAGS = {"unemployed", "fresher", "terminated", "job hopping", "gap", "no experience"}

# 🧠 Score and feedback logic
def score_hr(soft_skills, red_flags):
    score = 50
    score += len(soft_skills) * 10
    score -= len(red_flags) * 10
    return max(0, min(score, 100))  # bounded between 0–100

def feedback_hr(score, soft_skills, red_flags):
    feedback = []
    if soft_skills:
        feedback.append(f"Good soft skills: {', '.join(soft_skills)}.")
    if red_flags:
        feedback.append(f"Red flags: {', '.join(red_flags)}.")
    if score >= 80:
        feedback.append("Strong candidate overall.")
    elif score >= 50:
        feedback.append("Balanced profile. Review further.")
    else:
        feedback.append("Some concerns. Consider carefully.")
    return " ".join(feedback)

# 🤖 Main agent function
def hr_agent(resume):
    text = resume.get("clean_text", "").lower()

    soft_skills = sorted({skill for skill in SOFT_SKILLS if skill in text})
    red_flags = sorted({flag for flag in RED_FLAGS if flag in text})
    score = score_hr(soft_skills, red_flags)
    feedback = feedback_hr(score, soft_skills, red_flags)

    resume.update({
        "soft_skills": soft_skills,
        "red_flags": red_flags,
        "hr_score": score,
        "hr_feedback": feedback
    })
    return resume

# 🗂️ Batch processor
def batch_process_hr():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    processed = [hr_agent(resume) for resume in resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

    print(f"✅ HR Agent processed {len(processed)} resumes and saved to {OUTPUT_FILE}")
