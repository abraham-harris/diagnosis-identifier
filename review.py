import json
import icd10
from difflib import SequenceMatcher


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def evaluate_icd10_output(json_path):
    # Load output
    with open(json_path, "r") as f:
        data = json.load(f)

    results = []
    
    for entry in data["icd10"]:
        code = entry["code"]
        desc = entry["description"]
        evidence = entry["evidence"]

        # Validity check
        icd_obj = icd10.find(code)
        valid = icd_obj is not None

        # Canonical description (if valid)
        canonical_desc = icd_obj.description if valid else None

        # 3. Compare descriptions
        desc_similarity = (
            similarity(desc, canonical_desc) if valid else 0
        )

        results.append({
            "code": code,
            "valid": valid,
            "llm_description": desc,
            "canonical_description": canonical_desc,
            "description_similarity": desc_similarity,
            "evidence_count": len(evidence)
        })

    return results


if __name__ == "__main__":
    # Insert patient to check
    patient = "patient1"
    file_to_check = f"results/{patient}_icd10.json"

    results = evaluate_icd10_output(file_to_check)
    with open(f"results/{patient}_icd10_review.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)