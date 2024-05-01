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
from tenacity import retry, retry_if_result, stop_after_attempt, wait_fixed
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
    "OpenAI-Beta": "assistants=v2"
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
        "OpenAI-Beta": "assistants=v2"
    }

    response = requests.post(url, headers=headers)
    
    return response.json()

def is_failed_result(response):
    return response.status == "failed"
    

@retry(retry=retry_if_result(is_failed_result), 
       stop=stop_after_attempt(3), 
       wait=wait_fixed(2))
def get_completed_assistant_run(thread_id, run_id):
    
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    print(f"Checking run status: {run.status}")
    
    while run.status not in ["completed", "failed"]:
        time.sleep(15)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        print(f"Run status: {run.status}")
        
    if run.status == "failed":
        print("Failure reason:", run.last_error.message)
        print(f"Run: {run_id} Thread: {thread_id} \n FAILED RUN \n")
        return "failed"  # Returning the failed run for retry evaluation

    print("Outside of the if status failed: ", run.status)
    return run  # Completed runs are returned directly
        
def get_assistant_message(run_id, thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    
    
    most_recent = messages.data[0].content[0].text.value
    print(f"Run: {run_id} Thread: {thread_id} \n response: {most_recent} \n")
    return most_recent

def create_assistant(file_path, commodity, sign):
    assistant = client.beta.assistants.create(
        name="Get Extraction",
        instructions= instructions.replace("__COMMODITY__", commodity).replace("__SIGN__", sign),
        model="gpt-4-turbo",
        tools=[{"type": "file_search"}],
    )

    
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
    
    print(f"Created Assistant: {assistant.id}")
    return thread.id, assistant.id

def check_file(thread_id, assistant_id, file_path, commodity, sign):
    file_instructions = """If the file was correctly uploaded and can be read return YES otherwise return NO. 
                        Only return the Yes or No answer.
                        """
    run = client.beta.threads.runs.create(
      thread_id=thread_id,
      assistant_id=assistant_id,
      instructions= file_instructions
    )
    # print(f"Current run id = {run.id} thread_id = {thread_id}")
    
    ans = get_assistant_response(thread_id, run.id)
    print(f"Response: {ans}")
    if ans.lower() == "no":
        print("We need to reload file.")
        response_code = delete_assistant(assistant_id)
        if response_code == 200:
            print(f"Deleted assistant {assistant_id}")
        
        new_thread_id, new_assistant_id =  create_assistant(file_path, commodity, sign)
        return check_file(new_thread_id, new_assistant_id, file_path, commodity, sign)
    else:
        print("File was correctly uploaded \n")
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
                    print("Need to reformat the JSON extraction \n")
                    completion = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": "You are a json formatting expert"},
                        {"role": "user", "content": JSON_format_fix.replace("__INCORRECT__", json_str).replace("__CORRECT_SCHEMA__", correct_format)}
                    ]
                    ) 
                    return json.loads(completion.choices[0].message.content)         
    else:
        return None
    
def delete_all_files():
    response = client.files.list(purpose="assistants")
    for file in response.data:
        client.files.delete(file.id)
    print("Deleted any leftover files")
    
def read_csv_to_dict(file_path):
    data_dict_list = []
    
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            data_dict_list.append(dict(row))
    
    return data_dict_list

def is_array(s):
    return s.startswith('[') and s.endswith(']')

def clean_document_dict(document_dict_temp, title, url):
    key_to_remove = []

    for key, value in document_dict_temp.items():
        if isinstance(value, str):
            if value.strip() == "" and key != "doi":
                key_to_remove.append(key) 
        if key == 'title':
            document_dict_temp[key] = title
        
        if key == 'doi':
            if value != url:
                document_dict_temp[key] = url
        if key == 'authors':
            if isinstance(value, str):
                if value.strip()[0] == "[":
                    document_dict_temp[key] = [str(item.strip()).replace('"', "") for item in value[1:-1].split(',')]
                else:
                    document_dict_temp[key] = [str(item.strip()) for item in value.split(',')]  

    for key in key_to_remove:
        del document_dict_temp[key]

    return document_dict_temp

def clean_mineral_site_json(json_str, title, url):
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
             json_str["MineralSite"][0][key] = title
        if key == 'source_id':
            if value != url:
                json_str["MineralSite"][0][key] = url
        if key == 'location_info' and isinstance(value, dict):
            for new_key, new_value in value.items():
                if new_key == 'crs':
                    json_str["MineralSite"][0][key][new_key] = "EPSG:4326"
                    
                if new_key == 'location':
                    if isinstance(new_value, str) and (new_value.strip() == "" or new_value.strip() == "POINT()"):
                        key_to_remove.append((key, new_key))  # Append a tuple (key, new_key) for inner keys
                        key_to_remove.append((key, 'crs'))
                    

    for outer_key, inner_key in key_to_remove:
        if inner_key is None:
            if outer_key in json_str["MineralSite"][0]:
                del json_str["MineralSite"][0][outer_key]
        else:
            if outer_key in json_str["MineralSite"][0] and inner_key in json_str["MineralSite"][0][outer_key]:
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
    output_str = {"mineral_inventory":[]}
    grade_unit_list = list(unit_dict.keys())
    
    ## add conversion to tonnes
    
    for inner_dict in extraction_dict['extractions']:
        current_inventory_format = copy.deepcopy(inventory_format)
        changed_tonnage = False
    
        for key, value in inner_dict.items():
            if isinstance(value, int) or isinstance(value, float):
                value = str(value)
            
            elif 'category' in key:
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
                        
                output = check_instance(current_extraction=current_inventory_format, key = 'category', instance=list)
                if output is None:
                    current_inventory_format.pop('category')
                else:
                    current_inventory_format['category'] = output
            
            elif 'zone' in key:
                current_inventory_format['zone'] = value.lower()
                
            elif 'cut' in key.lower() and 'unit' not in key.lower():
                current_inventory_format['cutoff_grade']['grade_value'] = value.lower()
                output = check_instance(current_extraction=current_inventory_format['cutoff_grade'], key = 'grade_value', instance=float)
                if output is None:
                    current_inventory_format['cutoff_grade'].pop('grade_value')
                else:
                    current_inventory_format['cutoff_grade']['grade_value'] = output
                                                            
            elif 'cut' in key.lower() and 'unit' in key.lower():
                if value == '%':
                    current_inventory_format['cutoff_grade']['grade_unit'] = url_str + unit_dict['percent']
                elif value != '':
                    found_value = find_best_match(value, grade_unit_list[5:])
       
                    if found_value is not None:
                        current_inventory_format['cutoff_grade']['grade_unit'] = url_str + unit_dict[found_value]
                    
                output = check_instance(current_extraction=current_inventory_format['cutoff_grade'], key = 'grade_unit', instance=str)
                
                if output is None:
                    current_inventory_format['cutoff_grade'].pop('grade_unit')
                else:
                    current_inventory_format['cutoff_grade']['grade_unit'] = output
                    
                    
            elif 'tonnage' in key.lower() and 'unit' not in key.lower():
                value = value.replace(",", "")
                current_inventory_format['ore']['ore_value'] = value.lower()
                
                output = check_instance(current_extraction=current_inventory_format['ore'], key = 'ore_value', instance=float)
                if output is None:
                    current_inventory_format['ore'].pop('ore_value')
                else:
                    current_inventory_format['ore']['ore_value'] = output
               
            elif 'tonnage' in key.lower() and 'unit' in key.lower():
                
                ## check if in the kt values
                if value.lower() in kt_values:
                    value = "tonnes"
                    if current_inventory_format['ore']['ore_value']: 
                        float_val = float(current_inventory_format['ore']['ore_value']) * 1000
                        current_inventory_format['ore']['ore_value'] =  float_val
                        current_inventory_format['ore']['ore_unit'] = url_str + unit_dict[value]
                        changed_tonnage = True
                else:
                    found_value = find_best_match(value, grade_unit_list)
                    if found_value is not None:
                        print(f"Found match value for ore_unit {found_value}")
                        current_inventory_format['ore']['ore_unit'] = url_str + unit_dict[found_value.lower()]
                    else:
                        current_inventory_format['ore'].pop('ore_unit')
                output = check_instance(current_extraction=current_inventory_format['ore'], key = 'ore_unit', instance=str)
                if output is None:
                    current_inventory_format['ore'].pop('ore_unit')
                else:
                    current_inventory_format['ore']['ore_unit'] = output
                
            elif 'contained' in key.lower():
                if not current_inventory_format['ore'].get('ore_value') or not current_inventory_format['grade'].get('grade_value'):
                    current_inventory_format['contained_metal'] = ''
                else:
                    tonnes = float(current_inventory_format['ore']['ore_value'])
                    grade = float(current_inventory_format['grade']['grade_value'])
                    value = str(tonnes*grade/100)

                    if changed_tonnage: 
                        integer_value = float(value.lower())*1000
                        current_inventory_format['contained_metal'] = integer_value
                    else:
                        current_inventory_format['contained_metal'] = value.lower()
                    
                output =  check_instance(current_extraction=current_inventory_format, key = 'contained_metal', instance=float)
                if output is None:
                    current_inventory_format.pop('contained_metal')
                else:
                    current_inventory_format['contained_metal'] = output
                
            elif 'grade' in key.lower():
                
                current_inventory_format['grade']['grade_unit'] = url_str + unit_dict['percent']
                current_inventory_format['grade']['grade_value'] = value.lower()
                
                output = check_instance(current_extraction=current_inventory_format['grade'], key = 'grade_value', instance=float)
                if output is None:
                    current_inventory_format['grade'].pop('grade_value')
                    current_inventory_format['grade'].pop('grade_unit')
                else:
                    current_inventory_format['grade']['grade_value'] = output
                
            elif 'table' in key.lower():
                table_match = find_best_match(value.lower(), list(relevant_tables['Tables'].keys()), threshold = 70)
    
                if table_match is not None and isinstance(relevant_tables['Tables'][table_match], int):
                    current_inventory_format['reference']['page_info'][0]['page'] = relevant_tables['Tables'][table_match]
                else:
                    ## need to figure out best way to do this
                    current_inventory_format['reference']['page_info'][0].pop("page")

                output = check_instance(current_extraction=current_inventory_format['reference']['page_info'][0], key = 'page', instance=int)
                if output is None:
                    current_inventory_format['reference']['page_info'][0].pop('page')
                else:
                    current_inventory_format['reference']['page_info'][0]['page'] = output
            
        
            
                    
        current_inventory_format = check_empty_headers(current_inventory_format)        
        output_str["mineral_inventory"].append(current_inventory_format)
        
    return output_str

def check_empty_headers(extraction):
    keys_to_check = ["ore", "grade", "cutoff_grade"]
    
    for key in keys_to_check:
        if not extraction[key]:
            extraction.pop(key)
            print("Currently this value is empty")
    
    
    return extraction

def check_instance(current_extraction, key, instance):
    print(f"Previous value: {current_extraction}")

    if key in current_extraction:
        curr_value = current_extraction[key]
        print(f"Looking at key {key} : {curr_value}")
        
        ## want to test the current value or if its 0
        if isinstance(curr_value, str) and len(curr_value) == 0:
            ## in case we have an empty value should pop that value out
            output_value = None
        
        elif instance == float and isinstance(curr_value, str):
            curr_value = current_extraction[key]
            numeric_chars = re.findall(r'\d|\.', curr_value)
            str_value = ''.join(numeric_chars)
            curr_value = float(str_value)
    
        
        elif isinstance(curr_value, instance):
            output_value = current_extraction[key]
        else:
            try:
            # testing the current value as the instance
                output_value = instance(curr_value)
        
            except ValueError:
                print("Get value error")
                
    print("Outputted value: ", output_value)
    return output_value

def get_zotero(url):
    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, ZOLTERO_KEY)
    file_list = url.split("/")
    file_key = file_list[-1]
    file_item = zot.item(file_key)
    title = file_item['data']['title']
    print(f"Zoltero Information: file_key {file_key} Title: {title} \n")
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
        # print("Creating the thread")
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

        # print(f"Current run id = {run.id} thread_id = {thread_id}")

        # print("Retrieving the response\n")
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