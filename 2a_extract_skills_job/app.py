import os
import json
from openai import OpenAI
from ferris_ef import context

job_name = context.params.get("job_name")
job_industry = context.params.get("job_industry")

job_url = context.params.get("job_url") or ""
job_file = context.params.get("job_file") or ""
job_text = context.params.get("job_text") or ""

# Setup LangChain with OpenAI API
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
    prompt = f"The general industry context is {industry}. Extract and classify the skills from the following job description into hard skills, soft skills, and language skills. Eliminate all redundancies so each skill only shows up at maximum once in either category. Ensure that results are provided as a raw JSON key-value dictionary with no further complementary or cautionary text:\n\n{text}"
    response = client.chat.completions.create(model="gpt-3.5-turbo",  # Adjust the model as necessary (e.g. gpt-3.5-turbo)
    messages=[{"role": "system", "content": prompt}])
    # Accessing the last message in the completion which contains the response
    last_message = response.choices[0].message.content
    return last_message

# Concat job profile text from the environment params
job_profile_text = job_url + job_file + job_text

# Extract and classify skills
extracted_skills = extract_and_classify_skills(job_profile_text, job_industry)
skills_dict = normalize_keys(json.loads(extracted_skills))

print(skills_dict)

if skills_dict.get("hard_skills", []) or skills_dict.get("soft_skills", []) or skills_dict.get("language_skills", []):
    context.events.send(
        "ferris.apps.hr.job_extract",
        context.package.name,
        {
            "job": job_name,
            "job_industry": job_industry,
            "job_hard_skills": skills_dict.get("hard_skills", []),
            "job_soft_skills": skills_dict.get("soft_skills", []),
            "job_language_skills": skills_dict.get("language_skills", [])
        }
    )
    print("Job profiling step completed, Trigger Event: hr_coverage_ratio")
else:
    error_message = "Could not extract any skills from Job inputs."
    print(error_message)
    context.events.send(
        "ferris.apps.hr.job_error",
        context.package.name,
        {
            "job": job_name,
            "job_parsed_text": job_profile_text,
        }
    )

    print("Could not extract skills from Job input")