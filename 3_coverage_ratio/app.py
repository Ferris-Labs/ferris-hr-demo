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
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        # Accessing the last message in the completion which contains the response
        last_message = response.choices[0].message.content
        return last_message
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""


# Function to construct the OpenAI prompt
def create_skill_matching_prompt(job_data, candidate_data):
    prompt = (
        f"Given the job profile for a '{job_data['job_name']}' in the '{job_data['job_industry']}' industry "
        f"and the CV of a candidate with experience in the '{candidate_data['candidate_industry']}' industry, "
        "evaluate the skills for exact and partial matches. Classify the skills into 'Exact Matches', 'Partial Matches', "
        "'Missing Skills', and 'Additional Skills'. Flag any unique or highly specialized skills. Calculate the ratio of matched "
        "versus missing skills and calculate a second ratio for the overall fit of the candidate for the job."
        "Provide a brief text summary of the qualitative assessment of the match."
        "Output the results four skills categories as arrays (Matched Skills, Partial Skills, Missing Skills and Additional Skills),"
        "the two ratios and the assessment text. Consider the candidate experience in the qualititative assessment in addition to the skills."
        "Ensure that the results are provided as a raw JSON key-value dictionary with no further complementary or cautionary text."
        f"Following are the detailed skills from the job description:"
        f"Hard Skills: {job_data['job_hard_skills']}"
        f"Soft Skills: {job_data['job_soft_skills']}"
        f"Language Skills: {job_data['job_language_skills']}"
        f"Following are the detailed skills and the experience from the candidate:"
        f"Hard Skills: {candidate_data['candidate_hard_skills']}"
        f"Soft Skills: {candidate_data['candidate_soft_skills']}"
        f"Language Skills: {candidate_data['candidate_language_skills']}"
        f"Candidate Experience: {candidate_data['candidate_experience']}"
    )
    return prompt


# Main async function to execute the workflow
async def main():
    job_data = context.params.get("job_data")
    candidate_data = context.params.get("cand_data")

    # Create the prompt
    prompt = create_skill_matching_prompt(job_data, candidate_data)

    # Get the response from OpenAI
    skill_matching_response = await get_skill_matching_response(prompt)
    print("Response Type:", type(skill_matching_response))
    response_dict = json.loads(skill_matching_response)

    # Output handling
    print(json.dumps(response_dict, indent=4))  # For demonstration purposes

    print("End Script")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())