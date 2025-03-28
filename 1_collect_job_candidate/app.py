import os
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
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

# Context parameters
job_name = context.params.get("jobname")
job_industry = context.params.get("jobindustry")
job_url = context.params.get("joburl")
job_file = context.params.get("jobfile")
job_text = context.params.get("jobtext")

candidate_name = context.params.get("candname")
candidate_industry = context.params.get("candindustry")
candidate_url = context.params.get("candurl")
candidate_file = context.params.get("candfile")
candidate_text = context.params.get("candtext")

# Process local PDFs
job_profile_pdf_text = None
candidate_cv_pdf_text = None

if job_file:
    try:
        # Try different possible paths for the uploaded file
        possible_paths = [
            job_file,  # Direct path
            os.path.join(os.getcwd(), job_file),  # Current working directory
            os.path.join('/tmp', job_file),  # Temp directory
            os.path.join(os.path.dirname(__file__), job_file),  # Script directory
            os.path.join('/app', job_file)  # Container app directory
        ]
        
        job_file_path = None
        for path in possible_paths:
            print(f"Checking job file path: {path}")
            if os.path.exists(path):
                job_file_path = path
                break
        
        if job_file_path:
            job_profile_pdf_text = extract_text_from_pdf(job_file_path)
            print(f"Successfully read job PDF from: {job_file_path}")
        else:
            print(f"Job file not found in any of these locations: {possible_paths}")
    except Exception as e:
        print(f"Error processing job file: {str(e)}")
else:
    print("No job file provided")

if candidate_file:
    try:
        # Try different possible paths for the uploaded file
        possible_paths = [
            candidate_file,  # Direct path
            os.path.join(os.getcwd(), candidate_file),  # Current working directory
            os.path.join('/tmp', candidate_file),  # Temp directory
            os.path.join(os.path.dirname(__file__), candidate_file),  # Script directory
            os.path.join('/app', candidate_file)  # Container app directory
        ]
        
        cand_file_path = None
        for path in possible_paths:
            print(f"Checking candidate file path: {path}")
            if os.path.exists(path):
                cand_file_path = path
                break
        
        if cand_file_path:
            candidate_cv_pdf_text = extract_text_from_pdf(cand_file_path)
            print(f"Successfully read candidate PDF from: {cand_file_path}")
        else:
            print(f"Candidate file not found in any of these locations: {possible_paths}")
    except Exception as e:
        print(f"Error processing candidate file: {str(e)}")
else:
    print("No candidate file provided")

# Process URLs
job_profile_url_text = None
candidate_cv_url_text = None

if job_url:
    try:
        job_profile_url_text = extract_text_from_url(job_url)
        if job_profile_url_text:
            print(f"Successfully extracted text from job URL")
        else:
            print(f"Failed to extract text from job URL: {job_url}")
    except Exception as e:
        print(f"Error processing job URL: {str(e)}")
else:
    print("Job URL not provided")

if candidate_url:
    try:
        candidate_cv_url_text = extract_text_from_url(candidate_url)
        if candidate_cv_url_text:
            print(f"Successfully extracted text from candidate URL")
        else:
            print(f"Failed to extract text from candidate URL: {candidate_url}")
    except Exception as e:
        print(f"Error processing candidate URL: {str(e)}")
else:
    print("Candidate URL not provided")

# Combine all job profile text inputs with better logging
print("\nProcessing inputs:")
print(f"Job text input: {bool(job_text)}")
print(f"Job PDF text: {bool(job_profile_pdf_text)}")
print(f"Job URL text: {bool(job_profile_url_text)}")

print(f"Candidate text input: {bool(candidate_text)}")
print(f"Candidate PDF text: {bool(candidate_cv_pdf_text)}")
print(f"Candidate URL text: {bool(candidate_cv_url_text)}")

# Combine all job profile text inputs with priority order
job_profile_text = None
if job_text:
    job_profile_text = job_text
    print("Using direct job text input")
elif job_profile_pdf_text:
    job_profile_text = job_profile_pdf_text
    print("Using job PDF text")
elif job_profile_url_text:
    job_profile_text = job_profile_url_text
    print("Using job URL text")

# Combine all candidate profile text inputs with priority order
candidate_profile_text = None
if candidate_text:
    candidate_profile_text = candidate_text
    print("Using direct candidate text input")
elif candidate_cv_pdf_text:
    candidate_profile_text = candidate_cv_pdf_text
    print("Using candidate PDF text")
elif candidate_cv_url_text:
    candidate_profile_text = candidate_cv_url_text
    print("Using candidate URL text")

# For candidate data, if we have a file path but couldn't read it, try using it as direct text
if not candidate_profile_text and candidate_file:
    print("WARNING: Could not read candidate file as PDF, trying as direct text")
    candidate_profile_text = candidate_file

# Validate and send events with better error handling
success = True

if not job_profile_text:
    print("ERROR: No job description provided in any format (text, file, or URL)")
    success = False
else:
    try:
        context.events.send(
            "ferris.apps.hr.job_params",
            context.package.name,
            {
                "job": job_name,
                "job_industry": job_industry,
                "job_url": job_url,
                "job_file": job_profile_pdf_text,
                "job_text": job_profile_text,
            }
        )
        print(f"Successfully sent job data for {job_name}")
    except Exception as e:
        print(f"ERROR sending job data: {str(e)}")
        success = False

if not candidate_profile_text:
    print("ERROR: No candidate description provided in any format (text, file, or URL)")
    success = False
else:
    try:
        context.events.send(
            "ferris.apps.hr.candidate_params",
            context.package.name,
            {
                "candidate": candidate_name,
                "candidate_industry": candidate_industry,
                "candidate_url": candidate_url,
                "candidate_file": candidate_cv_pdf_text,
                "candidate_text": candidate_profile_text,
            }
        )
        print(f"Successfully sent candidate data for {candidate_name}")
    except Exception as e:
        print(f"ERROR sending candidate data: {str(e)}")
        success = False

if not success:
    print("Data collection completed with errors - check logs above")
    raise ValueError("Failed to send required events")
else:
    print("Data collection completed successfully")
