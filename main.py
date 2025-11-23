import os
import importlib
import re
from tqdm import tqdm
from agents import *

import agents
importlib.reload(agents)
from agents import *



def clean_quote(ev: str) -> str:
    """Remove extra white space and quotes from text."""
    ev = ev.strip()
    if (ev.startswith('"') and ev.endswith('"')) or \
       (ev.startswith("'") and ev.endswith("'")):
        ev = ev[1:-1]
    return ev.strip()

def keep_exact_quotes(icd10_output, med_record):
    """Ensure that all evidence is an exact quote."""
    med_lower = med_record.lower()
    cleaned_output = []
    removed = 0

    for item in icd10_output["icd10"]:
        cleaned_evidence = []
        for ev in item["evidence"]:
            ev_clean = clean_quote(ev)
            # Check if evidence appears exactly in the original document
            if ev_clean.lower() in med_lower:
                cleaned_evidence.append(ev_clean)
            else:
                removed += 1

        # Update evidence list
        item["evidence"] = cleaned_evidence
        cleaned_output.append(item)
    print(f"Number of evidences removed (inexact quotes): {removed}")
    return {"icd10": cleaned_output}

def chunk_paragraphs(text, max_chars=20000):
    """Split medical documents that are too long."""
    # Split on two or more newlines
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""

    for para in paragraphs:
        # Strip leading/trailing whitespace
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 2 <= max_chars:  # +2 for newline padding
            current += "\n\n" + para if current else para
        else:
            chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks



if __name__ == "__main__":
    # Set patient
    patient = "patient2"

    # Loop through data files
    outputs = []
    patient_data = f"data/synthetic_notes/{patient}/"
    files = os.listdir(patient_data)
    pbar = tqdm(total=len(files))
    for filename in files:

        # Read file
        with open(patient_data + filename, "r", encoding="utf-8") as f:
            med_record = f.read()

        # Chunk the text (to help fit in context windows)
        chunks = chunk_paragraphs(med_record, max_chars=15000)

        chunk_outputs = [] # collect output from each chunk
        for chunk in chunks:
            # Pass to coder
            coder_output = get_coder_output(chunk)

            # Pass coder output to reviewer
            reviewer_output = get_reviewer_output(chunk, coder_output)

            # Pass reviewer output to patient
            patient_output = get_patient_output(chunk, reviewer_output)

            # Pass reviewer output to physician
            physician_output = get_physician_output(chunk, reviewer_output)

            # Pass all outputs to adjustor
            adjuster_output = get_adjustor_output(chunk, coder_output, reviewer_output, patient_output, physician_output)

            # Ensure all quotes are exact
            file_output = keep_exact_quotes(json.loads(adjuster_output), chunk)
            chunk_outputs.extend(file_output["icd10"])
        
        # Merge chunk outputs with full list
        outputs.extend(chunk_outputs)
        
        
        pbar.update(1)
    pbar.close()

    # Combine all output data into final JSON 
    combined_output = {
        "icd10": outputs
    }
    
    # Handle duplicates
    deduped = {}
    for item in combined_output["icd10"]:
        code = item["code"]
        # Add type field
        item["type"] = "diagnosis"
        if code not in deduped:
            deduped[code] = item
        else:
            # Merge evidence lists
            existing = deduped[code]
            existing["evidence"] = list(set(existing["evidence"] + item["evidence"]))
    deduped_output = {"icd10": list(deduped.values())}

    # Save results
    with open(f"results/{patient}_icd10.json", "w", encoding="utf-8") as f:
        json.dump(deduped_output, f, indent=2)
    print(f"Output saved to 'results/{patient}_icd10.json'")