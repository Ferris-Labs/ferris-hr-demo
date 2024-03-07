import json
from openai import OpenAI
from ferris_ef import context

# Setup OpenAI API & Client
oai_key = context.secrets.get('OpenAI')['OPENAI_API_KEY']
client = OpenAI(api_key=oai_key)

def get_skill_matching_response(prompt):
    response = client.chat.completions.create(model = "gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}])
    # Accessing the last message in the completion which contains the response
    last_message = response.choices[0].message.content
    print(response.choices[0].message.content)
    return last_message


def normalize_keys(data):
    """Normalize keys in a dictionary to lowercase with underscores."""
    normalized_data = {}
    for key, value in data.items():
        normalized_key = key.lower().replace(" ", "_")
        normalized_data[normalized_key] = value
    return normalized_data


# Function to construct the OpenAI prompt
def create_skill_matching_prompt(job_data, candidate_data):
    prompt = (
        f"Given the job profile for a '{job_data['job_name']}' in the '{job_data['job_industry']}' industry "
        f"and the CV of a candidate with experience in the '{candidate_data['candidate_industry']}' industry, "
        "evaluate the skills for exact and partial matches. Classify the skills into 'Exact Matches', 'Partial Matches', "
        "'Missing Skills', and 'Additional Skills'. Flag any unique or highly specialized skills. Calculate the ratio of matched "
        "versus missing skills and calculate a second ratio for the overall fit of the candidate for the job."
        "Provide a brief text summary of the qualitative assessment of the match."
        "Output the results in a structured JSON format containing exactly four skills categories as arrays (Matched Skills,"
        "Partial Skills, Missing Skills and Additional Skills), the two ratios and the assessment text."
        f"Following are the detailed skills from the job description:"
        f"Hard Skills: {job_data['job_hard_skills']}"
        f"Soft Skills: {job_data['job_soft_skills']}"
        f"Language Skills: {job_data['job_language_skills']}"
        f"Following are the detailed skills from the candidate:"
        f"Hard Skills: {candidate_data['candidate_hard_skills']}"
        f"Soft Skills: {candidate_data['candidate_soft_skills']}"
        f"Language Skills: {candidate_data['candidate_language_skills']}"
    )
    return prompt


job_data = context.params.get("job_data")
candidate_data = context.params.get("cand_data")

# Create the prompt
prompt = create_skill_matching_prompt(job_data, candidate_data)

# Get the response from OpenAI
skill_matching_response = get_skill_matching_response(prompt)

response_dict = json.loads(skill_matching_response)

# Output handling
print(json.dumps(response_dict, indent=4))  # For demonstration purposes

print("End Script")