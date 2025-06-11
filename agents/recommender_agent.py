import sys
from pathlib import Path
import json

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ✅ Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "hr_output.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "final_recommendations.json"

# 🧮 Compute final weighted score
def compute_final_score(rec_score, ana_score, hr_score):
    # Weights can be tuned as needed
    return round(0.2 * rec_score + 0.5 * ana_score + 0.3 * hr_score, 2)

# 💬 Generate final recommendation
def generate_recommendation(score):
    if score >= 80:
        return "Highly recommended for interview."
    elif score >= 60:
        return "Recommended, meets most expectations."
    elif score >= 40:
        return "May be considered with reservations."
    else:
        return "Not recommended for this role."

# 🤖 Main agent
def recommender_agent(resume):
    rec_score = resume.get("recruiter_score", 0)
    ana_score = resume.get("analyst_score", 0)
    hr_score = resume.get("hr_score", 0)

    final_score = compute_final_score(rec_score, ana_score, hr_score)
    feedback = generate_recommendation(final_score)

    resume["recommendation_score"] = final_score
    resume["recommendation_feedback"] = feedback

    return resume

# 🗂️ Batch processor
def batch_process_recommender():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    final_output = [recommender_agent(resume) for resume in resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"✅ Final recommendations saved to {OUTPUT_FILE}")
