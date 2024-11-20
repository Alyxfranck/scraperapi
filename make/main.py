import requests
import json
import logging
import time
from datetime import datetime, timezone
import os

# Set up logging to output to both console and file
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set the logging level as needed

# Create handlers
console_handler = logging.StreamHandler()  # Console handler
log_directory = 'logs'
os.makedirs(log_directory, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_directory, 'scraper_log.log'), encoding='utf-8')  # File handler

# Set levels for handlers
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

# Create formatter and add it to handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Constants
SUBMIT_URL = "http://localhost/api/submit-scrape-job"
STATUS_URL_TEMPLATE = "http://localhost/api/job/{}"
AUTH_URL = "http://localhost/api/auth/token"  # Adjusted to the correct authentication endpoint
INDEX_TRACK_FILE = 'index.json'
MAX_RETRIES = 3
RETRY_DELAY = 2

# Variables
output_data = []
token = None

# Helper function to parse the business name from the URL
def parse_business_name(url):
    return '-'.join(url.rstrip('/').split('/')[-1].split('-')[:-1]).replace('-', ' ').title()

# Load or initialize the last processed index
def load_last_processed_index():
    try:
        with open(INDEX_TRACK_FILE, 'r') as file:
            index_data = json.load(file)
            return index_data.get("index", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

# Save the last processed index and log it
def save_last_processed_index(index):
    index_file_path = os.path.join(log_directory, INDEX_TRACK_FILE)
    with open(index_file_path, 'w') as file:
        json.dump({"index": index}, file)
    logger.info(f"Last processed index saved: {index}")

# Function to authenticate and retrieve the access token
def authenticate():
    global token
    try:
        response = requests.post(AUTH_URL, data={"username": "your_username", "password": "your_password"})
        response.raise_for_status()
        token_data = response.json()
        token = token_data.get("access_token")
        if token:
            logger.info("Successfully retrieved access token.")
        else:
            logger.error("Failed to retrieve access token.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication failed: {e}")

# Function to submit a scraping job
def submit_scraping_job(url_to_scrape):
    headers = {"Authorization": f"Bearer {token}"}
    job_data = {
        "id": "",
        "url": url_to_scrape,
        "elements": [
            {
                "name": "ContactSection",
                "xpath": '//*[@id="page-content"]/div/div/section[3]/div/div[4]',
                "url": url_to_scrape
            }
        ],
        "user": "",
        "time_created": datetime.now(timezone.utc).isoformat(),
        "result": [],
        "job_options": {
            "multi_page_scrape": False,
            "custom_headers": {}
        },
        "status": "Queued",
        "chat": ""
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(SUBMIT_URL, json=job_data, headers=headers)
            response.raise_for_status()
            job_id = response.json().get("id")
            
            if job_id:
                logger.info(f"Successfully submitted job for {url_to_scrape}, Job ID: {job_id}")
                return job_id
            else:
                logger.error(f"No job ID returned in response for {url_to_scrape}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit job for {url_to_scrape} on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
        
        time.sleep(RETRY_DELAY)
    
    logger.error(f"Could not submit job for {url_to_scrape} after {MAX_RETRIES} attempts.")
    return None

# Function to check the status of a job with added verification for list response
def check_job_status(job_id):
    headers = {"Authorization": f"Bearer {token}"}
    status_url = STATUS_URL_TEMPLATE.format(job_id)
    
    while True:
        try:
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()
            job_info = response.json()
            logger.debug(f"Job info for ID {job_id}: {job_info}")

            if isinstance(job_info, list):
                if job_info and isinstance(job_info[0], dict):
                    job_status = job_info[0].get("status")
                    result = job_info[0].get("result", [])
                else:
                    logger.warning(f"Unable to extract status information from list response for Job ID {job_id}")
                    return None
            elif isinstance(job_info, dict):
                job_status = job_info.get("status")
                result = job_info.get("result", [])
            else:
                logger.error(f"Unexpected format for Job ID {job_id}: {type(job_info)}")
                return None
            
            if job_status == "Completed":
                logger.info(f"Job ID {job_id} completed.")
                return result
            elif job_status == "Failed":
                logger.error(f"Job ID {job_id} failed.")
                return None
            else:
                logger.info(f"Job ID {job_id} is still in progress. Retrying...")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check status for Job ID {job_id}: {e}")
        
        time.sleep(RETRY_DELAY)

def process_result(result, url):
    contact_text = "No contact available"
    business_name = parse_business_name(url)  # Extract business name from the URL
    
    if result:
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    for key in item.keys():
                        if key.rstrip('/') == url.rstrip('/'):
                            url_data = item[key]
                            contact_section_data = url_data.get("ContactSection", [])
                            if contact_section_data:
                                first_element = contact_section_data[0]
                                if isinstance(first_element, dict):
                                    contact_text = first_element.get("text", "No contact available")
                                elif isinstance(first_element, str):
                                    contact_text = first_element
                            break
        elif isinstance(result, dict):
            contact_section = result.get("ContactSection", [])
            if contact_section:
                first_element = contact_section[0]
                if isinstance(first_element, dict):
                    contact_text = first_element.get("text", "No contact available")
                elif isinstance(first_element, str):
                    contact_text = first_element

    # Append to output_data with parsed business name
    contact_info = {
        "url": url,
        "business_name": business_name,
        "contact": contact_text
    }
    output_data.append(contact_info)
    logger.info(f"Data saved for {url}: {contact_info}")

# Main execution logic
try:
    authenticate()  # Obtain the access token at the start

    # Load URLs from the JSON file and the last processed index
    url_file_path = 'urls.json'
    with open(url_file_path, 'r', encoding='utf-8') as file:
        urls = json.load(file)
    
    last_index = load_last_processed_index()

    # Process each URL starting from the last processed index
    for i in range(last_index, len(urls)):
        url = urls[i]
        job_id = submit_scraping_job(url)
        
        if job_id:
            result = check_job_status(job_id)
            logger.debug(f"Scraped result for url: {url}, result: {result}")
            process_result(result, url)
            save_last_processed_index(i + 1)  # Save index after processing the URL
            time.sleep(RETRY_DELAY)  # Short delay between jobs
        else:
            logger.error(f"Skipping job for {url} due to submission failure.")

finally:
    # Save the extracted data to a JSON file
    output_directory = 'data'
    os.makedirs(output_directory, exist_ok=True)
    with open(os.path.join(output_directory, "contact_data.json"), "w", encoding='utf-8') as outfile:
        json.dump(output_data, outfile, indent=4, ensure_ascii=False)
    logger.info("Scraping complete, data saved to contact_data.json")
