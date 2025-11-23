import os
import importlib
from tqdm import tqdm
from agents import *

import agents
importlib.reload(agents)
from agents import *



if __name__ == "__main__":
    # Set patient
    patient = "patient1"

    # Loop through data files
    outputs = []
    patient_data = f"data/synthetic_notes/{patient}/"
    files = os.listdir(patient_data)
    pbar = tqdm(total=len(files))
    for filename in os.listdir(patient_data):

        # Read file
        with open(patient_data + filename, "r", encoding="utf-8") as f:
            med_record = f.read()

        # Pass to coder
        coder_output = get_coder_output(med_record)

        # # Pass coder output to reviewer
        # reviewer_output = get_reviewer_output(med_record, coder_output)

        # # Pass reviewer output to patient
        # patient_output = get_patient_output(med_record, reviewer_output)

        # # Pass reviewer output to physician
        # physician_output = get_physician_output(med_record, reviewer_output)

        # # Pass all outputs to adjustor
        # adjustor_output = get_adjustor_output(med_record, reviewer_output)

        outputs.extend(json.loads(coder_output)["icd10"])
        pbar.update(1)
    pbar.close()

    # Combine all output data into final JSON, TODO: handle duplicates
    final_output = {
        "icd10": outputs
    }
    print(final_output)

    with open(f"results/{patient}_icd10.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)