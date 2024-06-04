import os
import openai
import csv
from first_pass import prompts
from extraction_package import AssistantFunctions, GeneralFunctions
from settings import API_KEY, LIBRARY_ID, LIBRARY_TYPE, ZOLTERO_KEY 

client = openai.OpenAI(api_key = API_KEY)

def create_assistant_commodities(message_file_id):
    assistant = client.beta.assistants.create(
        name="Get Extraction",
        instructions= prompts.first_pass_instructions ,
        tools=[{"type": "file_search"}],
        model="gpt-4-1106-preview",
  
    )
    
    thread = client.beta.threads.create(
    messages=[
    {
      "role": "user",
      "content": "You are a geology expert and you are very good in understanding mining reports, which is attached.",
      "attachments": [{ "file_id": message_file_id, "tools": [{"type": "file_search"}] }]
    }]    
        
    )
    
    # print(f"Created an Assistant")
    return thread.id, assistant.id


def check_file_commodities(thread_id, assistant_id, file_path):
   
    ans = AssistantFunctions.get_assistant_message(thread_id, assistant_id, prompts.file_instructions)
    
    print(f"Response: {ans}")
    if ans.lower() == "no":
        print("We need to reload file.")
        response_code = AssistantFunctions.delete_assistant(assistant_id)
        if response_code == 200:
            print(f"Deleted assistant {assistant_id}")
        message_file = client.files.create(
              file=open(f"{file_path}", "rb"),
              purpose='assistants'
            )
        new_thread_id, new_assistant_id =  create_assistant_commodities(message_file.id)
        return check_file_commodities(new_thread_id, new_assistant_id, file_path)
    else:
        print("File was correctly uploaded \n")
        return thread_id, assistant_id
    
    
    
def add_to_metadata(csv_output_path, file_name, commodities_dict):
    
    if not os.path.exists(csv_output_path):
        # Create the CSV file with header row
        with open(csv_output_path, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['File Name', 'Identified Commodities'])

    with open(csv_output_path, mode='a', newline='') as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)
        
        if commodities_dict['commodities']:
            joined_commodities = ', '.join(commodities_dict['commodities'])
        else:
            joined_commodities = ""
        
        writer.writerow([file_name, joined_commodities])
    print(f"Finished writing row for {file_name} \n")