import os
import json
from groq import Groq
from pydantic import BaseModel
from typing import List


client = Groq(api_key=os.environ["GROQ_API_KEY"])
# Model options: {"openai/gpt-oss-20b", "openai/gpt-oss-120b", "meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct"
model = "meta-llama/llama-4-scout-17b-16e-instruct" 

# Output formatting
class ICD_code(BaseModel):
    code: str
    description: str
    evidence: List[str]

class ICD10(BaseModel):
    icd10: List[ICD_code]

class PatientPhysicianInstance(BaseModel):
    code: str
    explanation: str

class PatientPhysicianOutput(BaseModel):
    adjustments: List[PatientPhysicianInstance]

def normalize_icd10_json(raw):
    raw = json.loads(str(raw))
    # Case 1: Already correct
    if isinstance(raw, dict) and "icd10" in raw:
        return raw
    # Case 2: Bare list
    elif isinstance(raw, list):
        return {"icd10": raw}
    raise ValueError("Unexpected ICD10 JSON format")


def get_coder_output(data):
    """Reviews files to generate codes."""
    with open("data/prompts/coder.txt", "r") as f:
        prompt = f.read()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
               "role": "developer",
               "content": prompt
            },
            {
                "role": "user",
                "content": data
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "icd_code",
                "schema": ICD10.model_json_schema()
            }
        }
    )

    output = ICD10.model_validate(json.loads(response.choices[0].message.content))
    return output.model_dump_json(indent=2)


def get_reviewer_output(data, codes):
    """Reviews files and generated codes; makes adjustments if necessary."""
    with open("data/prompts/reviewer.txt", "r") as f:
        prompt = f.read()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
               "role": "developer",
               "content": prompt
            },
            {
                "role": "user",
                "content": f"Here is the medical document: \n###\n{data}\n###\nHere are the coder-assigned ICD-10 codes:\n###\n{codes}"
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "icd_code",
                "schema": ICD10.model_json_schema()
            }
        }
    )

    output = ICD10.model_validate(json.loads(response.choices[0].message.content))
    return json.dumps(output.model_dump(), indent=2)


def get_patient_output(data, codes):
    """Checks codes against files for errors and overcharges."""
    with open("data/prompts/patient.txt", "r") as f:
        prompt = f.read()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
               "role": "developer",
               "content": prompt
            },
            {
                "role": "user",
                "content": f"Here is your medical document: \n###\n{data}\n###\nHere are the assigned ICD-10 codes:\n###\n{codes}"
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "icd_code",
                "schema": PatientPhysicianOutput.model_json_schema()
            }
        }
    )

    output = PatientPhysicianOutput.model_validate(json.loads(response.choices[0].message.content))
    return json.dumps(output.model_dump(), indent=2)


def get_physician_output(data, codes):
    """Checks codes against files for errors and discrepancies."""
    with open("data/prompts/physician.txt", "r") as f:
        prompt = f.read()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
               "role": "developer",
               "content": prompt
            },
            {
                "role": "user",
                "content": f"Here is the medical document: \n###\n{data}\n###\nHere are the coder-assigned ICD-10 codes: \n###\n{codes}"
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "icd_code",
                "schema": PatientPhysicianOutput.model_json_schema()
            }
        }
    )

    output = PatientPhysicianOutput.model_validate(json.loads(response.choices[0].message.content))
    return json.dumps(output.model_dump(), indent=2)


def get_adjustor_output(data, coder_codes, reviewer_codes, patient_output, physician_output):
    """Adjusts final codes based on feedback from physician, patient, and reviewer."""
    with open("data/prompts/adjuster.txt", "r") as f:
        prompt = f.read()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
               "role": "developer",
               "content": prompt
            },
            {
                "role": "user",
                "content": f"Here is the medical document: \n###{data}\n###\nHere are the coder-assigned ICD-10 codes:\n###\n{coder_codes}\n###\nHere are the reviewer-assigned codes:\n###\n{reviewer_codes}\n###\nHere are the patient remarks:\n###\n{patient_output}\n###\nHere are the physician remarks:\n###\n{physician_output}"
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "icd_code",
                "schema": ICD10.model_json_schema()
            }
        }
    )

    adjusted_output = normalize_icd10_json(response.choices[0].message.content)
    output = ICD10.model_validate(adjusted_output)
    return json.dumps(output.model_dump(), indent=2)