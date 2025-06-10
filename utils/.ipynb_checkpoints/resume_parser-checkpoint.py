import os
import pathlib
import re
import docx
from pypdf import PdfReader
from collections import defaultdict

# ✅ Load spaCy English model (auto-download if needed)
import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# 📄 Extract text from PDF
def extract_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# 📄 Extract text from DOCX
def extract_from_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

# 📄 Generic extractor for any file
def extract_text(file_path: str) -> str:
    path = pathlib.Path(file_path)
    if path.suffix.lower() == ".pdf":
        return extract_from_pdf(str(path))
    elif path.suffix.lower() in {".docx", ".doc"}:
        return extract_from_docx(str(path))
    else:
        raise ValueError("Unsupported file format")

# 🔍 Parse text using spaCy & regex
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

    # 🎯 Extract basic skills (customize as needed)
    skills = re.findall(r"\b(python|java|sql|excel|pandas|tensorflow|aws|powerbi)\b", text, re.I)
    out["skills"] = list(set(map(str.lower, skills)))

    # Return preview text and full info
    out["raw"] = text[:2000]  # Preview text
    return dict(out)

# 🧪 Batch parse all resumes in /data/resumes and save to JSON
def batch_parse_resumes():
    import json

    RESUME_FOLDER = pathlib.Path(__file__).resolve().parents[1] / "data" / "resumes"
    OUTPUT_FILE = pathlib.Path(__file__).resolve().parents[1] / "data" / "recruiter_output.json"

    parsed_resumes = []
    for file in RESUME_FOLDER.iterdir():
        if file.suffix in [".pdf", ".docx"]:
            try:
                text = extract_text(file)
                parsed = parse_resume(text)
                parsed["file_name"] = file.name
                parsed_resumes.append(parsed)
            except Exception as e:
                print(f"❌ Error parsing {file.name}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed_resumes, f, indent=2)

    print(f"✅ Parsed {len(parsed_resumes)} resumes and saved to {OUTPUT_FILE}")
