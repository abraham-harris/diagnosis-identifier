import os
import json
from groq import Groq
from pydantic import BaseModel
from typing import List



client = Groq(api_key=os.environ["GROQ_API_KEY"])
model = "openai/gpt-oss-120b"

# Output formatting
class ICD_code(BaseModel):
    code: str
    description: str
    evidence: List[str]

class ICD10(BaseModel):
    icd10: List[ICD_code]


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
    return json.dumps(output.model_dump(), indent=2)


def get_adjustor_output(data, coder_codes, reviewer_codes, patient_codes, physician_codes):
    """Adjusts final codes based on feedback from physician, patient, and reviewer."""
    with open("data/prompts/adjustor.txt", "r") as f:
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
    return json.dumps(output.model_dump(), indent=2)