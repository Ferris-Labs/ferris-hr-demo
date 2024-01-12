import os
import json
from openai import OpenAI
from ferris_ef import context

candidate_name = context.params.get("candidate")
candidate_industry = context.params.get("candidate_industry")
candidate_url = context.params.get("candidate_url") or ""
candidate_file = context.params.get("candidate_file") or ""
candidate_text = context.params.get("candidate_text") or ""

# Setup OpenAI API & Client
oai_key = context.config.get('OPENAI_API_KEY')
client = OpenAI(api_key=oai_key)

def normalize_keys(data):
    """Normalize keys in a dictionary to lowercase with underscores."""
    normalized_data = {}
    for key, value in data.items():
        normalized_key = key.lower().replace(" ", "_")
        normalized_data[normalized_key] = value
    return normalized_data

# Function to extract and classify skills
def extract_and_classify_skills(text, industry):
    prompt = f"The general industry context is {industry}. Extract and classify the skills from the following candidate details and CV into hard skills, soft skills, and language skills. Eliminate all redundancies so each skill only shows up at maximum once in either category. Ensure that results are provided as a raw JSON key-value dictionary with no further complementary or cautionary text:\n\n{text}"
    response = client.chat.completions.create(model="gpt-3.5-turbo",  # Adjust the model as necessary (e.g. gpt-3.5-turbo)
    messages=[{"role": "system", "content": prompt}])
    # Accessing the last message in the completion which contains the response
    last_message = response.choices[0].message.content
    return last_message

# Concat job profile text from the environment params
cand_profile_text = candidate_url + candidate_file + candidate_text

# Extract and classify skills
extracted_skills = extract_and_classify_skills(cand_profile_text, candidate_industry)
skills_dict = normalize_keys(json.loads(extracted_skills))

print(skills_dict)

if skills_dict.get("hard_skills", []) or skills_dict.get("soft_skills", []) or skills_dict.get("language_skills", []):
    context.events.send(
        "ferris.apps.hr.cand_extract",
        context.package.name,
        {
            "candidate": candidate_name,
            "candidate_industry": candidate_industry,
            "candidate_hard_skills": skills_dict.get("hard_skills", []),
            "candidate_soft_skills": skills_dict.get("soft_skills", []),
            "candidate_language_skills": skills_dict.get("language_skills", [])
        }
    )
    print("Candidate profiling step completed, Trigger Event: hr_coverage_ratio")
else:
    error_message = "Could not extract any skills from candidate inputs."
    print(error_message)
    context.events.send(
        "ferris.apps.hr.cand_error",
        context.package.name,
        {
            "candidate": candidate_name,
            "job_parsed_text": cand_profile_text,
        }
    )

    print("Step Completed - Error")