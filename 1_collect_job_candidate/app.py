import os
from PyPDF2 import PdfReader
import requests
from io import BytesIO
from ferris_ef import context

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    if os.path.exists(pdf_path):
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    else:
        return None

# Function to download and extract text from PDF URL
def extract_text_from_pdf_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        reader = PdfReader(BytesIO(response.content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except requests.RequestException:
        return None
    
job = context.params.get("jobname")
job_industry = context.params.get("jobindustry")
job_url = context.params.get("joburl")
job_file = context.params.get("jobfile")
job_text = context.params.get("jobtext")

candidate = context.params.get("candname")
candidate_industry = context.params.get("candindustry")
candidate_url = context.params.get("candurl")
candidate_file = context.params.get("candfile")
candidate_text = context.params.get("candtext")

# Process local PDFs
job_profile_pdf_text = extract_text_from_pdf(job_file) if job_file else None
candidate_cv_pdf_text = extract_text_from_pdf(candidate_file) if candidate_file else None

# Process PDFs from URLs
job_profile_url_text = extract_text_from_pdf_url(job_url) if job_url else None
candidate_cv_url_text = extract_text_from_pdf_url(candidate_url) if candidate_url else None

if not (job_url or job_file or job_text):
    print("At least one of the three inputs needs to be provided for Job!")
if not (candidate_url or candidate_file or candidate_text):
    print("At least one of the three inpputs needs to be provided for Candidate!")

context.events.send(
    "ferris.apps.hr.job_cand_params",
    context.package.name,
    {
        "job": job,
        "job_industry": job_industry,
        "job_url": job_profile_url_text,
        "job_file": job_profile_pdf_text,
        "job_text": job_text,
        "candidate": candidate,
        "candidate_industry": candidate_industry,
        "candidate_url": candidate_cv_url_text,
        "candidate_file": candidate_cv_pdf_text,
        "candidate_text": candidate_text,
    }
)

print(f"Issuing a skills extraction and classification for {job} and {candidate}.")
print(f"Sending skills event for next step.")
