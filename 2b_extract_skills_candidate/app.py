import os
import json
import asyncio
from openai import AsyncOpenAI
from ferris_ef import context

candidate_name = context.params.get("candidate")
candidate_industry = context.params.get("candidate_industry")
candidate_url = context.params.get("candidate_url") or ""
candidate_file = context.params.get("candidate_file") or ""
candidate_text = context.params.get("candidate_text") or ""

# Setup OpenAI API & Client
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
        f"The general industry context is {industry}. Extract and classify the skills from the following candidate profile "
        "into four categories: hard skills, soft skills, language skills, and experience. Eliminate all redundancies so each skill "
        "only shows up at most once in either category. Exclude any terms that are not skills from the skills entries. Ensure that "
        "results are provided as a raw JSON key-value dictionary with no further complementary or cautionary text. "
        "Structure the JSON as follows and do not change the key names:\n"
        "{\n"
        '  "hard_skills": ["hard_skill1", "hard_skill2", ...],\n'
        '  "soft_skills": ["soft_skill1", "soft_skill2", ...],\n'
        '  "language_skills": ["language_skill1", "language_skill2", ...],\n'
        '  "experience": [{"company": "company_a", "from": "from_time_1", "to": "to_time_2"}, {"company": "company_b", "from": "from_time_3", "to": "to_time_4"}, ...]\n'        "}\n\n"
        f"Candidate description:\n{text}"
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        # Accessing the message content from the response
        last_message = response.choices[0].message.content
        return last_message
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""

# Main async function to execute the workflow
async def main():
    try:
        # Concat candidate profile text from the environment params
        cand_profile_text = candidate_text or candidate_file or candidate_url
        
        if not cand_profile_text:
            raise ValueError("No candidate description provided in any format (text, file, or URL)")

        # Extract and classify skills
        extracted_skills = await extract_and_classify_skills(cand_profile_text, candidate_industry)

        if not extracted_skills:
            raise ValueError("No skills were extracted from the candidate profile")

        try:
            extracted_skills = extracted_skills.strip()
            if extracted_skills.startswith("```json") and extracted_skills.endswith("```"):
                extracted_skills = extracted_skills[7:-3].strip()
            print(f"Processed Output for JSON Loading: {extracted_skills}")
            skills_dict = json.loads(extracted_skills)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse extracted skills as JSON: {str(e)}")

        if not any([
            skills_dict.get("hard_skills", []),
            skills_dict.get("soft_skills", []),
            skills_dict.get("language_skills", [])
        ]):
            raise ValueError("No valid skills found in any category")

        # Send success event
        context.events.send(
            "ferris.apps.hr.cand_extract",
            context.package.name,
            {
                "candidate": candidate_name,
                "candidate_industry": candidate_industry,
                "candidate_hard_skills": skills_dict.get("hard_skills", []),
                "candidate_soft_skills": skills_dict.get("soft_skills", []),
                "candidate_language_skills": skills_dict.get("language_skills", []),
                "candidate_experience": skills_dict.get("experience", [])
            }
        )
        print("Candidate profiling completed successfully")

    except Exception as e:
        error_message = str(e)
        print(f"Error in candidate processing: {error_message}")
        context.events.send(
            "ferris.apps.hr.cand_error",
            context.package.name,
            {
                "candidate": candidate_name,
                "candidate_parsed_text": cand_profile_text if 'cand_profile_text' in locals() else "",
                "error": error_message
            }
        )
        print("Step Completed - Error")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
