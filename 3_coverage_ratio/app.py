import json
from openai import OpenAI
from ferris_ef import context

# Setup OpenAI API & Client
oai_key = context.secrets.get('OpenAI')['OPENAI_API_KEY']
client = OpenAI(api_key=oai_key)

def get_skill_matching_response(prompt):
    try:
        # Using the openai.ChatCompletion.create method according to the latest API
        response = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            promtp = prompt,
            max_tokens = 1500,
            n = 1,
            stop = None
        )
        # Assuming the response structure is correctly returned by the API
        if response and 'choices' in response and len(response['choices']) > 0:
            text = response['choices'][0]['text'].strip()
            if text:
                return text
            else:
                print("No valid text received from OpenAI.")
                return "{}"
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "{}"


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

response_dict = normalize_keys(json.loads(skill_matching_response))

# Output handling
print(json.dumps(response_dict, indent=4))  # For demonstration purposes

print("End Script")