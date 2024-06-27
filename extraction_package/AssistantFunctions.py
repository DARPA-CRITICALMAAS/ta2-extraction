import openai
import requests
import json
import time
import warnings
import requests
from tenacity import retry, retry_if_result, stop_after_attempt, wait_fixed
from requests.exceptions import ConnectionError
import logging
from settings import API_KEY,MODEL_TYPE 
from extraction_package.Prompts import *
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')
client = openai.OpenAI(api_key = API_KEY)
    
logger = logging.getLogger("Assistant") 

def create_assistant(file_path):
    assistant = client.beta.assistants.create(
        name="Get Extraction",
        instructions= instructions,
        model=MODEL_TYPE,  ## try new model
        tools=[{"type": "file_search"}],
    )

    logger.info(f"Created the assistant with Model: {MODEL_TYPE}")
    message_file = client.files.create(
    file=open(file_path, "rb"), purpose="assistants"
    )

    thread = client.beta.threads.create(
    messages=[
    {
    "role": "user",
    "content": "You are a geology expert and you are very good in understanding mining reports, which is attached.",
    "attachments": [
        { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
    ],
    }])
    
    logger.info(f"Created Assistant: {assistant.id}")
    return thread.id, assistant.id, message_file.id

def create_new_thread(message_file_id, content):
    
    thread = client.beta.threads.create(
    messages=[
    {
    "role": "user",
    "content": content,
    
    "attachments": [
        { "file_id": message_file_id, "tools": [{"type": "file_search"}] }
    ],
    }])
    logger.debug(f"Creating new_thread {thread.id} with content : {content} \n")
    return thread.id
    

def fix_formats(json_str, correct_format):
    logger.info("Need to reformat the JSON extraction \n")
    completion = client.chat.completions.create(
    model=MODEL_TYPE,
    messages=[
        {"role": "system", "content": "You are a json formatting expert"},
        {"role": "user", "content": JSON_format_fix.replace("__INCORRECT__", json_str).replace("__CORRECT_SCHEMA__", correct_format)}
    ],
    response_format={'type': "json_object"}
    ) 
    return json.loads(completion.choices[0].message.content) 
    
def check_file(thread_id, assistant_id, message_file_id, file_path):
    ans = get_assistant_message(thread_id, assistant_id, file_instructions)
    
    logger.info(f"Response: {ans}")
    
    if ans.lower() == "no":
        logger.debug("We need to reload file.")
        response_code = delete_assistant(assistant_id)
        if response_code == 200:
            logger.debug(f"Deleted assistant {assistant_id}")
        
        new_thread_id, new_assistant_id, new_message_file_id =  create_assistant(file_path)
        logger.debug("Created new_thread")
        return check_file(new_thread_id, new_assistant_id, new_message_file_id, file_path)
    else:
        logger.debug("File was correctly uploaded \n")
        return thread_id, assistant_id, message_file_id

def delete_assistant(assistant_id):
    url = f"https://api.openai.com/v1/assistants/{assistant_id}"

    # Set up headers with your API key
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "OpenAI-Beta": "assistants=v2"
    }
    assistant = True

    # Make the DELETE request
    while assistant:
        try:
            response = requests.delete(url, headers=headers)

            if response.status_code == 200:
                logger.info(f"Assistant : {assistant_id} was deleted")
                assistant = False
            else:
                logger.debug("Retrying to delete assistant...")
                time.sleep(1)  # Wait for 1 second before retrying
                
        except Exception as e:
            logger.error("An error occurred:", e)
            time.sleep(1)  # Wait for 1 second before retrying

    

def is_failed_result(response):
    if isinstance(response, ConnectionError):
        # Log the connection error and return True to trigger retry
        logger.error(f"Connection error occurred: {response}")
        return True
    
    # Check if the response status indicates failure
    logger.debug(f"is_failed_result: Response: {response.status} type {type(response.status)}")
    return response.status == "failed"


@retry(retry=retry_if_result(is_failed_result), 
    stop=stop_after_attempt(6), 
    wait=wait_fixed(2))
def get_created_assistant_run(thread_id, assistant_id, prompt):
    
    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions= prompt
    )
    # logger.debug(f"Current prompt being used: {prompt} \n")
    
    while run.status not in ["completed", "failed"]:
        time.sleep(15)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        logger.info(f"Run status: {run.status}")
        
    if run.status == "failed":
        logger.error("Failure reason:", run.last_error.message)
        logger.error(f"Run: {run.id} Thread: {thread_id} \n FAILED RUN \n")

    print()
    return run  # Completed runs are returned directly
        
def get_assistant_message(thread_id, assistant_id, prompt):
    run = get_created_assistant_run(thread_id, assistant_id, prompt)
    
    messages = client.beta.threads.messages.list(thread_id=thread_id)

    most_recent = messages.data[0].content[0].text.value
    logger.info(f"Run: {run.id} Thread: {thread_id} \n response: {most_recent} \n")
    return most_recent


def delete_all_files():
    response = client.files.list(purpose="assistants")
    for file in response.data:
        client.files.delete(file.id)
    logger.info("Deleted any leftover files")



