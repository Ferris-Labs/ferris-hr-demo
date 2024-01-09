import os
import json
import openai
from ferris_ef import context

job_name = context.params.get("job_name")
company_name = context.params.get("companyname") or ""
man_url = context.params.get("profile_url") or ""
location = context.params.get("location") or ""

# Setup LangChain with OpenAI API
# openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_key = "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"

# Function to extract and classify skills
def extract_and_classify_skills(text):
    prompt = f"Extract and classify the skills from the following job description into hard skills, soft skills, and language skills. Eliminate all redundancies so each skill only shows up at maximum once in either category. Ensure that results are provided as a raw JSON key-value dictionary with no further complementary or cautionary text:\n\n{text}"
    response = openai.Completion.create(
        engine="text-davinci-003",  # or another appropriate model
        prompt=prompt,
        max_tokens=250  # Adjust as necessary
    )
    return response.choices[0].text.strip()

# Retrieve job profile text from the environment
job_profile_text = context.params.get("job_url") + context.params.get("job_file") + context.params.get("job_text")

# Extract and classify skills
extracted_skills = extract_and_classify_skills(job_profile_text)

# Assuming the model's response is formatted as a JSON string
skills_dict = json.loads(extracted_skills)

# Create extended JSON dictionary
data = {
    "job": job_name,
    "job_hard_skills": skills_dict.get("hard_skills", []),
    "job_soft_skills": skills_dict.get("soft_skills", []),
    "job_language_skills": skills_dict.get("language_skills", [])
}

if data["job_hard_skills"] or data["job_soft_skills"] or data["job_language_skills"]:
    context.events.send(
        "hr_job_extract",
        context.package.name,
        {
            data
        }
    )
    print("Job profiling step completed, Trigger Event: hr_coverage_ratio")
else:
    error_message = "Could not extract any skills from Job inputs."
    print(error_message)
    context.events.send(
        "hr_job_error",
        context.package.name,
        {
            "job": job_name,
            "job_parsed_text": job_profile_text,
        }
    )

    print("Could not extract skills from Job input")