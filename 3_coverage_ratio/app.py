import json
import asyncio
from openai import AsyncOpenAI
from ferris_ef import context

# Setup OpenAI API & Client
oai_key = context.secrets.get('OpenAI')['OPENAI_API_KEY']
client = AsyncOpenAI(api_key=oai_key)

# Function to get skill matching response
async def get_skill_matching_response(prompt):
    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        last_message = response.choices[0].message.content
        return last_message
    except Exception as e:
        print(f"Error during API call: {e}")
        raise ValueError(f"OpenAI API error: {str(e)}")

# Function to construct the OpenAI prompt
def create_skill_matching_prompt(job_data, candidate_data):
    prompt = (
        "Analyze the following job and candidate profiles and provide a structured JSON response with the following format:\n"
        "{\n"
        '  "exact_matches": ["skill1", "skill2"],\n'
        '  "partial_matches": ["skill3", "skill4"],\n'
        '  "missing_skills": ["skill5", "skill6"],\n'
        '  "additional_skills": ["skill7", "skill8"],\n'
        '  "skills_match_ratio": 7.5,\n'
        '  "overall_fit_ratio": 8.2,\n'
        '  "assessment": "Detailed qualitative assessment text"\n'
        "}\n\n"
        f"Job Profile:\n"
        f"- Title: {job_data['job_name']}\n"
        f"- Industry: {job_data['job_industry']}\n"
        f"- Hard Skills: {job_data['job_hard_skills']}\n"
        f"- Soft Skills: {job_data['job_soft_skills']}\n"
        f"- Language Skills: {job_data['job_language_skills']}\n\n"
        f"Candidate Profile:\n"
        f"- Industry: {candidate_data['candidate_industry']}\n"
        f"- Hard Skills: {candidate_data['candidate_hard_skills']}\n"
        f"- Soft Skills: {candidate_data['candidate_soft_skills']}\n"
        f"- Language Skills: {candidate_data['candidate_language_skills']}\n"
        f"- Experience: {candidate_data['candidate_experience']}\n\n"
        "Consider synonyms and related skills as matches. Both ratios should be on a scale of 0-10. "
        "Include experience assessment in the overall fit ratio."
    )
    return prompt

# Main async function to execute the workflow
async def main():
    try:
        # Get and validate input data
        job_data = context.params.get("job_data")
        candidate_data = context.params.get("cand_data")

        if not job_data or not candidate_data:
            raise ValueError("Missing required job or candidate data")

        required_job_fields = ['job_name', 'job_industry', 'job_hard_skills', 'job_soft_skills', 'job_language_skills']
        required_candidate_fields = ['candidate_industry', 'candidate_hard_skills', 'candidate_soft_skills', 
                                   'candidate_language_skills', 'candidate_experience']

        if not all(field in job_data for field in required_job_fields):
            raise ValueError(f"Missing required job fields. Required: {required_job_fields}")
        
        if not all(field in candidate_data for field in required_candidate_fields):
            raise ValueError(f"Missing required candidate fields. Required: {required_candidate_fields}")

        # Create the prompt and get response
        prompt = create_skill_matching_prompt(job_data, candidate_data)
        skill_matching_response = await get_skill_matching_response(prompt)

        # Process response
        skill_matching_response = skill_matching_response.strip()
        if skill_matching_response.startswith("```json") and skill_matching_response.endswith("```"):
            skill_matching_response = skill_matching_response[7:-3].strip()

        try:
            response_dict = json.loads(skill_matching_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI response as JSON: {str(e)}")

        # Validate response structure
        required_response_fields = ['exact_matches', 'partial_matches', 'missing_skills', 
                                  'additional_skills', 'skills_match_ratio', 'overall_fit_ratio', 
                                  'assessment']
        
        if not all(field in response_dict for field in required_response_fields):
            raise ValueError(f"Invalid response format. Missing required fields: {required_response_fields}")

        # Send results event
        context.events.send(
            "ferris.apps.hr.coverage_result",
            context.package.name,
            {
                "job_name": job_data['job_name'],
                "candidate_name": candidate_data.get('candidate_name', 'Unknown'),
                "results": response_dict
            }
        )

        print("Analysis completed successfully")
        print(json.dumps(response_dict, indent=4))

    except Exception as e:
        error_message = str(e)
        print(f"Error in coverage ratio analysis: {error_message}")
        context.events.send(
            "ferris.apps.hr.coverage_error",
            context.package.name,
            {
                "job_data": job_data if 'job_data' in locals() else None,
                "candidate_data": candidate_data if 'candidate_data' in locals() else None,
                "error": error_message
            }
        )
        raise  # Re-raise to ensure the error is properly logged

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())