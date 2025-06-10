import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import re

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "analyst_output.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "hr_output.json"

# === Rules
SOFT_SKILLS = [
    "communication", "teamwork", "leadership", "adaptability",
    "problem solving", "creativity", "time management",
    "collaboration", "interpersonal", "critical thinking"
]

RED_FLAGS = [
    "fresher", "no experience", "job hopping", "unemployed",
    "terminated", "fired", "laid off", "gap"
]

# === HR Agent
def hr_agent(resume: dict) -> dict:
    text = resume.get("clean_text", "").lower()
    
    found_soft_skills = [s for s in SOFT_SKILLS if s in text]
    found_red_flags = [r for r in RED_FLAGS if re.search(r"\b" + re.escape(r) + r"\b", text)]

    resume["soft_skills"] = found_soft_skills
    resume["red_flags"] = found_red_flags

    return resume

# === Batch runner
def batch_process_hr():
    if not INPUT_FILE.exists():
        print(f"❌ Input file missing: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    enriched = [hr_agent(resume) for resume in resumes]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)

    print(f"✅ HR Agent processed {len(enriched)} resumes and saved to {OUTPUT_FILE}")
