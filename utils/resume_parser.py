import os
import json
import re
import docx
from pathlib import Path
from pypdf import PdfReader
from collections import defaultdict
import spacy

# ✅ Load the model directly (it will be installed via requirements.txt)
nlp = spacy.load("en_core_web_sm")

# 📁 Path setup
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_FOLDER = PROJECT_ROOT / "data" / "resumes"
OUTPUT_FILE = PROJECT_ROOT / "data" / "recruiter_output.json"

# 📄 Extract from PDF
def extract_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# 📄 Extract from DOCX
def extract_from_docx(file_path: Path) -> str:
    doc = docx.Document(str(file_path))
    return "\n".join([para.text for para in doc.paragraphs])

# 📄 Universal extractor
def extract_text(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        return extract_from_pdf(file_path)
    elif file_path.suffix.lower() == ".docx":
        return extract_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.name}")

# 🔍 Parse resume text with spaCy + regex
def parse_resume(text: str) -> dict:
    doc = nlp(text)
    out = defaultdict(list)

    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG"}:
            out["names_orgs"].append(ent.text)
        elif ent.label_ == "GPE":
            out["locations"].append(ent.text)
        elif ent.label_ == "DATE":
            out["dates"].append(ent.text)

    skills = re.findall(r"\b(python|sql|excel|pandas|tensorflow|aws|powerbi|communication|django)\b", text, re.I)
    out["skills"] = list(set(map(str.lower, skills)))
    out["raw"] = text[:2000]
    return dict(out)

# 🚀 Batch parse all resumes
def batch_parse_resumes():
    all_parsed = []

    if not RESUME_FOLDER.exists():
        print(f"❌ Folder not found: {RESUME_FOLDER}")
        return

    for file in RESUME_FOLDER.iterdir():
        if file.suffix.lower() in [".pdf", ".docx"]:
            try:
                text = extract_text(file)
                parsed = parse_resume(text)
                parsed["file_name"] = file.name
                all_parsed.append(parsed)
            except Exception as e:
                print(f"⚠️ Error processing {file.name}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_parsed, f, indent=2)

    print(f"✅ Parsed {len(all_parsed)} resumes and saved to {OUTPUT_FILE}")
