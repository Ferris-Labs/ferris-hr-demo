import os
import json
import asyncio
from openai import AsyncOpenAI
from ferris_ef import context

job_name = context.params.get("job")
job_industry = context.params.get("job_industry")

job_url = context.params.get("job_url") or ""
job_file = context.params.get("job_file") or ""
job_text = context.params.get("job_text") or ""

# Setup OpenAI API
oai_key = context.secrets.get('OpenAI')['OPENAI_API_KEY']
client = AsyncOpenAI(api_key=oai_key)

def normalize_keys(data):
    """Normalize keys in a dictionary to lowercase with underscores."""
    normalized_data = {}
    for key, value in data.items():
        normalized_key = key.lower().replace(" ", "_")
        normalized_data[normalized_key] = value
    return normalized_data

# Function to extract and classify skills
async def extract_and_classify_skills(text, industry):
    prompt = (
        f"The general industry context is {industry}. Extract and classify the skills from the following job description "
        "into hard skills, soft skills, and language skills. Eliminate all redundancies so each skill only shows up at most "
        "once in either category. Exclude company names that are not skills. Ensure that results are provided as a raw JSON "
        "key-value dictionary with no further complementary or cautionary text. Structure the JSON as follows:\n"
        "{\n"
        '  "hard_skills": ["specific technical skills or knowledge related to the job"],\n'
        '  "soft_skills": ["interpersonal and personal attributes"],\n'
        '  "language_skills": ["languages required or beneficial"]\n'
        "}\n\n"
        "Job description:\n"
        f"{text}"
    )
    try:
        response = await client.chat_completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        # Accessing the message content from the response
        last_message = response.choices[0].message['content']
        return last_message
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""

# Main async function to execute the workflow
async def main():
    # Concat job profile text from the environment params
    job_profile_text = job_text or job_file or job_url

    # Extract and classify skills
    extracted_skills = await extract_and_classify_skills(job_profile_text, job_industry)

    # Logging the extracted skills for debugging purposes
    print("Extracted Skills Raw Output:")
    print(extracted_skills)

    if extracted_skills:
        try:
            skills_dict = normalize_keys(json.loads(extracted_skills))
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            skills_dict = {}

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
            print("Step Completed - Error")
    else:
        print("No skills were extracted.")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
