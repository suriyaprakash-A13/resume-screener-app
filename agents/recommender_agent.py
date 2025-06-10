import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "hr_output.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "final_recommendations.json"

# === Recommender Logic
def recommender_agent(resume: dict) -> dict:
    score = resume.get("match_score", 0)

    # Bonus for soft skills
    soft_skills = resume.get("soft_skills", [])
    score += 2 * len(soft_skills)

    # Penalty for red flags
    red_flags = resume.get("red_flags", [])
    score -= 5 * len(red_flags)

    # Normalize score between 0 and 100
    score = max(0, min(100, score))
    resume["recommendation_score"] = round(score, 2)
    return resume

# === Batch Processor
def batch_process_recommender():
    if not INPUT_FILE.exists():
        print(f"❌ Input file missing: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    scored = [recommender_agent(r) for r in resumes]
    ranked = sorted(scored, key=lambda x: x["recommendation_score"], reverse=True)

    top_5 = ranked[:5]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(top_5, f, indent=2)

    print(f"✅ Top 5 candidates saved to {OUTPUT_FILE}")
