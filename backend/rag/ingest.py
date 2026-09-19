from __future__ import annotations
import json, re, hashlib
from pathlib import Path
import fitz

HEADER_RE = re.compile(r"^(?:[A-Z][A-Z0-9 /&'(),.-]{4,}|\d+(?:\.\d+)*\.?\s+.+)$")

def normalize(text: str) -> str:
    text = text.replace("\u201f", '"').replace("\u201d", '"').replace("\u2019", "'")
    return re.sub(r"\s+", " ", text).strip()

def infer_section(text: str, current: str) -> str:
    for line in [x.strip() for x in text.splitlines() if x.strip()]:
        if HEADER_RE.match(line) and len(line) <= 110 and not line.endswith('.'):
            if line.upper() in {"UNIVERSAL SOMPO GENERAL INSURANCE CO LTD", "CSC- INDIVIDUAL HEALTH INSURANCE- POLICY WORDING"}:
                continue
            if line[:1].isdigit() or line.isupper():
                return line[:110]
    return current or "Policy wording"

def chunk_policy(pdf_path: str, out_path: str, max_chars: int = 2600) -> list[dict]:
    doc = fitz.open(pdf_path)
    chunks=[]; section="Policy wording"
    for pno, page in enumerate(doc, start=1):
        raw=page.get_text("text")
        section=infer_section(raw, section)
        # Prefer paragraph boundaries and preserve page-level traceability.
        paras=[normalize(p) for p in re.split(r"\n\s*\n|\n(?=\d+\.)", raw) if normalize(p)]
        buf=""
        for para in paras:
            candidate=(buf+" "+para).strip()
            if len(candidate)>max_chars and buf:
                cid=hashlib.sha1(f"{pno}:{section}:{buf}".encode()).hexdigest()[:12]
                chunks.append({"chunk_id":f"p{pno:02d}-{cid}","page":pno,"section":section,"text":buf})
                buf=para
            else: buf=candidate
        if buf:
            cid=hashlib.sha1(f"{pno}:{section}:{buf}".encode()).hexdigest()[:12]
            chunks.append({"chunk_id":f"p{pno:02d}-{cid}","page":pno,"section":section,"text":buf})
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_text(json.dumps(chunks,indent=2,ensure_ascii=False),encoding='utf-8')
    return chunks

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--pdf',default='policy/source/USGIC-CSCIndividualHealthInsurance_2017-2018.pdf'); ap.add_argument('--out',default='policy/processed/chunks.json'); args=ap.parse_args()
    chunks=chunk_policy(args.pdf,args.out); print(f"Created {len(chunks)} policy chunks")
