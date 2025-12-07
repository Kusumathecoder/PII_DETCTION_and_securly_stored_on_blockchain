import re
import hashlib
import logging
import tempfile
from typing import List, Dict
from PIL import Image
import pytesseract
import fitz  # PyMuPDF for PDF text + image extraction
import spacy
from transformers import pipeline

logger = logging.getLogger(__name__)

# -------------------------
# Load NLP Models Once
# -------------------------

nlp = spacy.load("en_core_web_trf")
ml_ner_pipeline = pipeline(
    "ner",
    model="dslim/bert-base-NER",
    tokenizer="dslim/bert-base-NER",
    grouped_entities=True,
)

# -------------------------
# Regex Patterns
# -------------------------
REGEX_PATTERNS = [
    (r"\b\d{4}\s\d{4}\s\d{4}\b", "AADHAAR"),
    (r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "PAN"),
    (r"\b[A-Z]{3}[0-9]{7}\b", "VOTER_ID"),
    (r"\+91[-\s]?\d{10}\b", "PHONE"),
    (r"\b[6-9]\d{9}\b", "PHONE"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "EMAIL"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b\d{6}\b", "PIN_CODE"),
]

# -------------------------
# Helper: SHA-256 Hash
# -------------------------
def sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

# -------------------------
# OCR/Text Extraction (No Poppler)
# -------------------------
def extract_text(fileobj):
    """
    Extract text from PDF or image using PyMuPDF (fitz) and Tesseract OCR.
    Works on Windows without Poppler.
    """
    name = fileobj.name.lower()
    with tempfile.NamedTemporaryFile(delete=False,
                                     suffix=".pdf" if name.endswith(".pdf") else ".png") as tmp:
        tmp.write(fileobj.read())
        path = tmp.name

    try:
        if name.endswith(".pdf"):
            text = ""
            with fitz.open(path) as pdf:
                for page in pdf:
                    # Extract digital text (if any)
                    text += page.get_text("text") or ""
                    # If text is empty or page has images, apply OCR
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img, lang="eng")
                    if ocr_text.strip():
                        text += "\n" + ocr_text
            return text
        else:
            image = Image.open(path).convert("RGB")
            return pytesseract.image_to_string(image, lang="eng")
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""

# -------------------------
# Regex Detection
# -------------------------
def detect_regex(text):
    results, seen = [], set()
    for pattern, label in REGEX_PATTERNS:
        for match in re.finditer(pattern, text):
            ent = match.group().strip()
            key = (ent.lower(), label)
            if key not in seen and len(ent) > 2:
                seen.add(key)
                results.append({
                    "Entity": ent,
                    "Label": label,
                    "Source": "Regex",
                    "hash": sha256_hash(ent)
                })
    return results

# -------------------------
# spaCy Detection
# -------------------------
def detect_spacy(text):
    doc = nlp(text)
    results = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "NORP", "DATE"]:
            results.append({
                "Entity": ent.text,
                "Label": ent.label_,
                "Source": "spaCy",
                "hash": sha256_hash(ent.text)
            })
    return results

# -------------------------
# BERT Detection
# -------------------------
def detect_bert(text):
    try:
        ents = ml_ner_pipeline(text)
        results = []
        for ent in ents:
            entity_text = ent["word"].replace("##", "").strip()
            if len(entity_text) >= 2:
                results.append({
                    "Entity": entity_text,
                    "Label": ent.get("entity_group", "UNKNOWN"),
                    "Source": "BERT",
                    "hash": sha256_hash(entity_text),
                    "Confidence": round(ent["score"], 2)
                })
        return results
    except Exception as e:
        logger.error(f"BERT detection failed: {e}")
        return []

# -------------------------
# Merge Detections
# -------------------------
def merge_detections(*all_lists):
    merged = {}
    for detections in all_lists:
        for d in detections:
            key = (d["Entity"].lower(), d["Label"])
            merged[key] = d
    return list(merged.values())

# -------------------------
# Redaction
# -------------------------
# -------------------------
# Redaction (fixed keys)
# -------------------------
def redact_text(text: str, detections: List[Dict], placeholder_format: str = "[REDACTED:{type}]") -> str:
    if not detections:
        return text
    redacted = text
    for d in sorted(detections, key=lambda x: text.find(x["match"]), reverse=True):
        entity = d["match"]
        placeholder = placeholder_format.format(**d)
        redacted = re.sub(re.escape(entity), placeholder, redacted)
    return redacted

# -------------------------
# Main Public API
# -------------------------
def detect_pii(text: str) -> List[Dict]:
    """Unified PII detection pipeline (Regex + spaCy + BERT)."""
    if not text:
        return []
    regex_r = detect_regex(text)
    spacy_r = detect_spacy(text)
    bert_r = detect_bert(text)
    merged = merge_detections(regex_r, spacy_r, bert_r)
    formatted = [{"type": d["Label"], "match": d["Entity"], "hash": d["hash"]} for d in merged]
    return formatted

def detect_and_redact_pii(text: str):
    detections = detect_pii(text)
    redacted = redact_text(text, detections)
    return redacted, detections
