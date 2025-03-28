import os
import json
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from ferris_ef import context

job_name = context.params.get("job_name")
job_url = context.params.get("job_url") or ""
job_file = context.params.get("job_file") or ""
job_text = context.params.get("job_text") or ""

# Setup LangChain with OpenAI API
# openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_key = "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"
llm = OpenAI(api_key=openai_api_key)

# Define the prompt template
template = "Extract and classify the skills from the following job description into hard skills, soft skills, and language skills. Eliminate all redundancies so each skill only shows up at maximum once in either category. Ensure that results are provided as a raw JSON key-value dictionary with no further complementary or cautionary text:\n\n{job_description}"
prompt = PromptTemplate(template=template, input_variables=["job_description"])

# Create the chain
llm_chain = LLMChain(prompt=prompt, llm=llm)

# Concat job profile text from the environment params
job_profile_text = job_url + job_file + job_text


# Run the chain
response = llm_chain.run({"job_description": job_profile_text})
extracted_skills = response.output.strip()

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