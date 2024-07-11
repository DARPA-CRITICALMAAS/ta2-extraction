import os
import openai
import csv
import requests
import json
import logging
import logging.config
from first_pass import prompts
from extraction_package import AssistantFunctions
from settings import API_KEY, CDR_BEARER, MODEL_TYPE 

logging.config.fileConfig('config.ini')
logger = logging.getLogger("Helper") 

client = openai.OpenAI(api_key = API_KEY)

def download_document(doc_id, download_dir):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+ CDR_BEARER
    }

    url_pdf = f'https://api.cdr.land/v1/docs/document/{doc_id}'
    url_meta = f'https://api.cdr.land/v1/docs/document/meta/{doc_id}'
    logger.debug("in download document")

    # Send the initial GET request
    response = requests.get(url_meta, headers=headers)
    logger.info(f"Meta doc status code: {response.status_code}")
    if response.status_code == 200:
        # Save the response content to a file
        resp_json = json.loads(response.content)
        title = resp_json['title']
        
        response = requests.get(url_pdf, headers=headers)

        if response.status_code == 200:    
            with open(f'{download_dir}{doc_id}_{title}.pdf', 'wb') as file:
                file.write(response.content)
            logger.info(f"Document downloaded and saved as '{title}.pdf'")
        else:
            logger.info(f"Failed to download document. Status code: {response.status_code}")
    else:
        logger.info(f"Failed to get meta data. Status code: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        

def create_assistant_commodities(message_file_id):
    assistant = client.beta.assistants.create(
        name="Get Extraction",
        instructions= prompts.first_pass_instructions ,
        tools=[{"type": "file_search"}],
        model=MODEL_TYPE,
  
    )
    
    thread = client.beta.threads.create(
    messages=[
    {
      "role": "user",
      "content": "You are a geology expert and you are very good in understanding mining reports, which is attached.",
      "attachments": [{ "file_id": message_file_id, "tools": [{"type": "file_search"}] }]
    }]    
        
    )
    
    # logger.info(f"Created an Assistant")
    return thread.id, assistant.id


def check_file_commodities(thread_id, assistant_id, file_path):
   
    ans = AssistantFunctions.get_assistant_message(thread_id, assistant_id, prompts.file_instructions)
    
    logger.info(f"Response: {ans}")
    if ans.lower() == "no":
        logger.info("We need to reload file.")
        response_code = AssistantFunctions.delete_assistant(assistant_id)
        if response_code == 200:
            logger.info(f"Deleted assistant {assistant_id}")
        message_file = client.files.create(
              file=open(f"{file_path}", "rb"),
              purpose='assistants'
            )
        new_thread_id, new_assistant_id =  create_assistant_commodities(message_file.id)
        return check_file_commodities(new_thread_id, new_assistant_id, file_path)
    else:
        logger.info("File was correctly uploaded \n")
        return thread_id, assistant_id
    
    
    
def add_to_metadata(csv_output_path, file_name, record_id, commodities_dict):
    
    if not os.path.exists(csv_output_path):
        # Create the CSV file with header row
        with open(csv_output_path, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['File Name', 'record_id', 'Identified Commodities'])

    with open(csv_output_path, mode='a', newline='') as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)
        
        if commodities_dict['commodities']:
            joined_commodities = ', '.join(commodities_dict['commodities'])
        else:
            joined_commodities = ""
        
        writer.writerow([file_name, record_id, joined_commodities])
    logger.info(f"Finished writing row for {file_name} \n")