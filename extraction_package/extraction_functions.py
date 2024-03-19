import openai
import requests
import json
import os
import time
import warnings
import re
import csv
import requests
from pyzotero import zotero
import copy
from fuzzywuzzy import process
from settings import API_KEY, LIBRARY_ID, LIBRARY_TYPE, ZOLTERO_KEY 
from extraction_package.prompts import *
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

client = openai.OpenAI(api_key = API_KEY)

def delete_assistant(assistant_id):
    url = f"https://api.openai.com/v1/assistants/{assistant_id}"

    # Set up headers with your API key
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "OpenAI-Beta": "assistants=v1"
    }

    # Make the DELETE request
    response = requests.delete(url, headers=headers)

    # Print the response content
    return response.status_code


def cancel_assistant_run(thread_id,run_id):
    
    url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/cancel"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v1"
    }

    response = requests.post(url, headers=headers)
    
    return response.json()

def get_assistant_response(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(thread_id=thread_id,run_id=run_id)
    print(f"Checking run status: {run.status}")
    while run.status != "completed":
        time.sleep(15)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id,run_id=run_id)
        
    print("Run is completed. Printing the entire thread now in sequential order \n")
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    
#     for thread_message in messages.data[::-1]:
#         run_id_value = thread_message.run_id
#         content_value = thread_message.content[0].text.value
#         print(f"{run_id_value}: {content_value} \n")
    
    
    most_recent = messages.data[0].content[0].text.value
    print(f"Most run {run_id} response: {most_recent} ")
    return most_recent

def create_assistant(file_id):
    assistant = client.beta.assistants.create(
        name="Get Extraction",
        instructions= instructions.replace("__COMMODITY__", os.environ.get('commodity')).replace("__SIGN__", os.environ.get('sign')),
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[file_id]
    )

    thread = client.beta.threads.create(
    messages=[
    {
      "role": "user",
      "content": "You are a geology expert and you are very good in understanding mining reports, which is attached.",
      "file_ids": [file_id]
    }])
    print(f"Created an Assistant")
    return thread.id, assistant.id

def check_file(thread_id, assistant_id):
    file_instructions = """If the file was correctly uploaded and can be read return YES otherwise return NO. 
                        Only return the Yes or No answer.
                        """
    run = client.beta.threads.runs.create(
      thread_id=thread_id,
      assistant_id=assistant_id,
      instructions= file_instructions
    )
    print(f"Current run id = {run.id} thread_id = {thread_id}")
    
    ans = get_assistant_response(thread_id, run.id)
    print(f"Response: {ans}")
    if ans.lower() == "no":
        print("We need to reload file.")
        response_code = delete_assistant(assistant_id)
        if response_code == 200:
            print(f"Deleted assistant {assistant_id}")
        file = client.files.create(
              file=open(f"./reports/{os.environ.get('file_path')}", "rb"),
              purpose='assistants'
            )
        new_thread_id, new_assistant_id =  create_assistant(file.id)
        return check_file(new_thread_id, new_assistant_id)
    else:
        print("File was correctly uploaded")
        return thread_id, assistant_id

def extract_json_strings(input_string, correct_format, remove_comments = False):
    start = input_string.find('{')
    if start != -1:
        # Remove comments starting with // or # since we get a lot in the return
        if remove_comments: 
            input_string = re.sub(r'(?<!["\'])//.*?\n|/\*.*?\*/|(#.*?\n)', '', input_string)
        
        count = 0
        for i in range(start, len(input_string)):
            if input_string[i] == '{':
                count += 1
            elif input_string[i] == '}':
                count -= 1
            if count == 0:
                json_str = input_string[start:i+1]
                # print(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    # here is the error, lets fix this
                    print("Need to fix the JSON extraction")
                    completion = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": "You are a json formatting expert"},
                        {"role": "user", "content": json_format_fix.replace("__INCORRECT__", json_str).replace("__CORRECT_SCHEMA__", correct_format)}
                    ],
                    response_format={'type': "json_object"}
                    ) 
                    return json.loads(completion.choices[0].message.content)         
    else:
        return None
    
def read_csv_to_dict(file_path):
    data_dict_list = []
    
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            data_dict_list.append(dict(row))
    
    return data_dict_list

def is_array(s):
    return s.startswith('[') and s.endswith(']')

def clean_document_dict(document_dict_temp):
    key_to_remove = []

    for key, value in document_dict_temp.items():
        if isinstance(value, str):
            if value.strip() == "" and key != "doi":
                key_to_remove.append(key) 
        if key == 'title':
            document_dict_temp[key] = os.environ.get("title")
        
        if key == 'doi':
            if value != os.environ.get("url"):
                document_dict_temp[key] = os.environ.get("url")
        if key == 'authors':
            if isinstance(value, str):
                if value.strip()[0] == "[":
                    document_dict_temp[key] = [str(item.strip()).replace('"', "") for item in value[1:-1].split(',')]
                else:
                    document_dict_temp[key] = [str(item.strip()) for item in value.split(',')]  

    for key in key_to_remove:
        del document_dict_temp[key]

    return document_dict_temp

def clean_mineral_site_json(json_str):
    # cycle through dict
    key_to_remove = []

    for key, value in json_str["MineralSite"][0].items():
        # print(f"Here is the key {key}, value {value}")
        if isinstance(value, str):
            if value.strip() == "" and key != "source_id" and key != "record_id":
                key_to_remove.append((key, None))  # Append a tuple (key, None) for outer keys
        if key == 'record_id':
            json_str["MineralSite"][0][key] = "1"
        
        if key == 'name':
             json_str["MineralSite"][0][key] = os.environ.get("title")
        if key == 'source_id':
            if value != os.environ.get("url"):
                json_str["MineralSite"][0][key] = os.environ.get("url")
        if key == 'location_info' and isinstance(value, dict):
            for new_key, new_value in value.items():
                if isinstance(new_value, str) and (new_value.strip() == "" or new_value.strip() == "POINT()"):
                    key_to_remove.append((key, new_key))  # Append a tuple (key, new_key) for inner keys
                    key_to_remove.append((key, 'crs'))

    for outer_key, inner_key in key_to_remove:
        if inner_key is None:
            del json_str["MineralSite"][0][outer_key]
        else:
            del json_str["MineralSite"][0][outer_key][inner_key]

    return json_str
    
    
def find_best_match(input_str, list_to_match, threshold=75):
    # Get the best match and its score
    best_match, score = process.extractOne(input_str, list_to_match)

    # Check if the score is above the threshold
    if score >= threshold:
        return best_match
    else:
        return None


def create_mineral_inventory_json(extraction_dict, inventory_format, relevant_tables, unit_dict):
    kt_values = ["k","kt", "000s tonnes", "thousand tonnes", "thousands", "000s" , "000 tonnes"]
    url_str = "https://minmod.isi.edu/resource/"
    output_str = {"MineralInventory":[]}
    grade_unit_list = list(unit_dict.keys())
    
    ## add conversion to tonnes
    
    for inner_dict in extraction_dict['extractions']:
        current_inventory_format = copy.deepcopy(inventory_format)
        changed_tonnage = False
    
        for key, value in inner_dict.items():
            
            if 'category' in key:
                current_inventory_format['category'] = []
                acceptable_values = ["inferred", "indicated","measured", "probable", 
                "proven", "proven+probable", "inferred+indicated", "inferred+measured",
                "measured+indicated"]
               
                if value.lower() in acceptable_values:
                    if "+" in value.lower():
                        new_vals = value.lower().split("+")
                        for val in new_vals:
                            current_inventory_format['category'].append(url_str + val.lower())
                    else:
                        current_inventory_format['category'].append(url_str + value.lower())
            
            elif 'zone' in key:
                current_inventory_format['zone'] = value.lower()
                
            elif 'cut' in key.lower() and 'unit' not in key.lower():
                current_inventory_format['cutoff_grade']['grade_value'] = value.lower()
            
            elif 'cut' in key.lower() and 'unit' in key.lower():
                if value == '%':
                    current_inventory_format['cutoff_grade']['grade_unit'] = url_str + unit_dict['percent']
                elif value != '':
                    found_value = find_best_match(value, grade_unit_list[5:])
       
                    if found_value is not None:
                        current_inventory_format['cutoff_grade']['grade_unit'] = url_str + unit_dict[found_value]
                    else:
                        current_inventory_format['cutoff_grade']['grade_unit'] = ''
                else:
                    current_inventory_format['cutoff_grade']['grade_unit'] = ''
            
            elif 'tonnage' in key.lower() and 'unit' not in key.lower():
                current_inventory_format['ore']['ore_value'] = value.lower()
          
            
            elif 'tonnage' in key.lower() and 'unit' in key.lower():
                if value.lower() in kt_values:
                    value = "tonnes"
                    float_val = float(current_inventory_format['ore']['ore_value']) * 1000
                    current_inventory_format['ore']['ore_value'] =  str(float_val)
                    current_inventory_format['ore']['ore_unit'] = url_str + unit_dict[value]
                    changed_tonnage = True
                else:
                    found_value = find_best_match(value, grade_unit_list)
                    if found_value is not None:
                        current_inventory_format['ore']['ore_unit'] = url_str + unit_dict[found_value.lower()]
                    else:
                        current_inventory_format['ore']['ore_unit'] = ''
                
                # print(f"After looking at tonnage unit {current_inventory_format['ore']['ore_value']}")
                
            elif 'contained' in key.lower():
                tonnes = float(current_inventory_format['ore']['ore_value'])
                grade = float(current_inventory_format['grade']['grade_value'])
                value = str(tonnes*grade/100)

                if changed_tonnage: 
                    integer_value = float(value.lower())*1000
                    current_inventory_format['contained_metal'] = str(integer_value)
                else:
                    current_inventory_format['contained_metal'] = value.lower()
                
            elif 'grade' in key.lower():
                current_inventory_format['grade']['grade_unit'] = url_str + unit_dict['percent']
                current_inventory_format['grade']['grade_value'] = value.lower()
                
            elif 'table' in key.lower():
                    table_match = find_best_match(value.lower(), list(relevant_tables['Tables'].keys()), threshold = 70)
        
                    if table_match is not None:
                        current_inventory_format['reference']['page_info'][0]['page'] = relevant_tables['Tables'][table_match]
                    else:
                        print("Need to find correct Page number for current table: ", value)
                        
        if current_inventory_format['cutoff_grade']['grade_unit'] == '' and current_inventory_format['cutoff_grade']['grade_value'] == '':
            current_inventory_format.pop('cutoff_grade')
            
        output_str["MineralInventory"].append(current_inventory_format)
        
    return output_str

def get_zotero(url):
    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, ZOLTERO_KEY)
    file_list = url.split("/")
    file_key = file_list[-1]
    file_item = zot.item(file_key)
    title = file_item['data']['title']
    print(f"file_key {file_key} Title: {title}")
    return title

def format_deposit_candidates(deposit_list):
    deposit_type_candidate = { "deposit_type_candidate": []}
    
    for dep in deposit_list['deposit_type'].keys():
        inner_dict = {}
        inner_dict["observed_name"] = dep
        inner_dict["normalized_uri"] = deposit_list['deposit_type'][dep]
        inner_dict["source"] = "report" 
        inner_dict["confidence"] = 1/len(deposit_list['deposit_type']) 
        deposit_type_candidate['deposit_type_candidate'].append(inner_dict)
        
    return deposit_type_candidate
        
        
def extract_by_category(commodity, commodity_sign, dictionary_format, curr_cat, relevant_tables, thread_id, assistant_id, done_first):
    if relevant_tables is not None and len(relevant_tables['Tables']) > 0:
        print("Creating the thread")
        if not done_first:
            use_instructions = find_category_rows.replace("__RELEVANT__", str(relevant_tables)).replace("__CATEGORY__", curr_cat).replace("__COMMODITY__", commodity).replace("__MINERAL_SIGN__", commodity_sign).replace("__DICTIONARY_FORMAT__", dictionary_format)
        else:
            use_instructions = find_additional_categories.replace("__RELEVANT__", str(relevant_tables)).replace("__CATEGORY__", curr_cat).replace("__DICTIONARY_FORMAT__", dictionary_format)
            
        # print(use_instructions)
        run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=use_instructions
        )

        print(f"Current run id = {run.id} thread_id = {thread_id}")

        print("Retrieving the response\n")
        ans = get_assistant_response(thread_id, run.id)


        extraction_dict = extract_json_strings(ans, dictionary_format, remove_comments = True)

        return extraction_dict

    else:
        return None
    
def convert_int_or_float(obj):
    if isinstance(obj, dict):
        return {key: convert_int_or_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_int_or_float(item) for item in obj]
    elif isinstance(obj, (int, float)):
        return obj
    elif isinstance(obj, str) and obj.isdigit():
        return int(obj)
    elif isinstance(obj, str) and obj.replace('.', '', 1).isdigit():
        return float(obj)
    return obj