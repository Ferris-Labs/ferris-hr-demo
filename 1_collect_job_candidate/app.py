import os
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import requests
from io import BytesIO
from ferris_ef import context
from ferris_cli.v2 import FerrisEvents

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    if os.path.exists(pdf_path):
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    else:
        print(f"File does not exist: {pdf_path}")
        return None

# Function to download and extract text from PDF URL
def extract_text_from_pdf_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        if response.headers['Content-Type'] != 'application/pdf':
            print(f"URL does not point to a PDF file: {url}")
            return None
        reader = PdfReader(BytesIO(response.content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except requests.RequestException as e:
        print(f"Request failed for URL: {url}, error: {e}")
        return None
    except PyPDF2.errors.PdfReadError as e:
        print(f"Failed to read PDF from URL: {url}, error: {e}")
        return None

# Function to extract text from HTML URL
def extract_text_from_html_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        if 'text/html' not in response.headers['Content-Type']:
            print(f"URL does not point to an HTML page: {url}")
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator='\n')
        return text
    except requests.RequestException as e:
        print(f"Request failed for URL: {url}, error: {e}")
        return None

# Process PDFs or HTML from URLs
def extract_text_from_url(url):
    pdf_text = extract_text_from_pdf_url(url)
    if pdf_text is not None:
        return pdf_text
    html_text = extract_text_from_html_url(url)
    return html_text


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
if job_file:
    script_dir = os.getcwd()
    rel_path = job_file
    job_file_path = os.path.join(script_dir, rel_path)
    job_profile_pdf_text = extract_text_from_pdf(job_file_path)
    print(job_profile_pdf_text)
else:
    print(f"Job file not provided: {job_file}")
    job_profile_pdf_text = None

if candidate_file:
    script_dir = os.getcwd()
    rel_path = candidate_file
    cand_file_path = os.path.join(script_dir, rel_path)
    candidate_cv_pdf_text = extract_text_from_pdf(cand_file_path)
    print(candidate_cv_pdf_text)
else:
    print(f"Candidate file not provided: {candidate_file}")
    candidate_cv_pdf_text = None

# Process job and candidate URLs
job_profile_url_text = extract_text_from_url(job_url) if job_url else None
candidate_cv_url_text = extract_text_from_url(candidate_url) if candidate_url else None

if not (job_url or job_file or job_text):
    print("At least one of the three inputs needs to be provided for Job!")
if not (candidate_url or candidate_file or candidate_text):
    print("At least one of the three inputs needs to be provided for Candidate!")

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
