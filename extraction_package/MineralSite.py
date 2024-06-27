import json
import warnings
import logging
import re
import pandas as pd
import extraction_package.Prompts as prompts
import extraction_package.SchemaFormats as schemas
import extraction_package.AssistantFunctions as assistant
import extraction_package.GeneralFunctions as general
from settings import URL_STR
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger("Site") 

def create_document_reference(thread_id, assistant_id, record_id, title):
    # thread_id, assistant_id = assistant.create_assistant(file_path, commodity, sign)

    # thread_id, assistant_id = assistant.check_file(thread_id, assistant_id, file_path, commodity, sign)

    document_ref = schemas.created_document_ref(title)
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.name_instructions.replace('__DOCUMENT_REF___', document_ref))

    document_dict_temp = general.extract_json_strings(ans, document_ref)
    document_dict = clean_document_dict(document_dict_temp, title)
    doc_name = document_dict.get('title', '')   


    print(f" Here is the reference material for the document: \n {document_dict} \n")
    
    site_format = schemas.create_mineral_site(record_id, doc_name=doc_name)
    
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.loc_instructions.replace('__SITE_FORMAT__', site_format))
    
    mineral_site_json = general.extract_json_strings(ans, site_format)
    if mineral_site_json is None:
        mineral_site_json = json.loads(site_format)
        

    mineral_site_json = clean_mineral_site_json(mineral_site_json, title, record_id)

    print(f"Here is the Mineral Site Json: \n {mineral_site_json} \n")
    
    # assistant.delete_assistant(assistant_id)
        
    return document_dict, mineral_site_json

def clean_document_dict(document_dict_temp, title):
    key_to_remove = []

    for key, value in document_dict_temp.items():
        if isinstance(value, str):
            if value.strip() == "":
                key_to_remove.append(key) 
        if key == 'title':
            document_dict_temp[key] = title
        
        if key == 'authors':
            if isinstance(value, str):
                if value and len(value.strip()) > 0 and value.strip()[0] == "[":
                    document_dict_temp[key] = [str(item.strip()).replace('"', "") for item in value[1:-1].split(',')]
                else:
                    document_dict_temp[key] = [str(item.strip()) for item in value.split(',')]  

    for key in key_to_remove:
        del document_dict_temp[key]

    return document_dict_temp
    

def clean_mineral_site_json(json_str, title, record_id):
    # cycle through dict
    key_to_remove = []

    for key, value in json_str.items():
        # print(f"Here is the key {key}, value {value}")
        if isinstance(value, str):
            if value.strip() == "" and key != "source_id" and key != "record_id":
                key_to_remove.append((key, None))  # Append a tuple (key, None) for outer keys
        if key == 'record_id':
            json_str[key] = record_id
        
        if key == 'name':
            json_str[key] = title
            
        if key == 'source_id':
           json_str[key] = "https://api.cdr.land"
                
        if key == 'location_info' and isinstance(value, dict):
            for new_key, new_value in value.items():
                if new_key == 'crs':
                    json_str[key][new_key] = URL_STR + "Q701"
                    
                if new_key == 'location':
                    if isinstance(new_value, str) and (new_value.strip() == "" or new_value.strip() == "POINT()") or not is_valid_point(new_value):
                        key_to_remove.append((key, new_key))  # Append a tuple (key, new_key) for inner keys
                        key_to_remove.append((key, 'crs'))
                        
                if new_key == 'country':
                    
                    if new_value == "": 
                        key_to_remove.append((key, new_key))
                    else:
                       country_temp = new_value
                       json_str = add_country_or_state("country.csv", json_str, key, new_key, new_value, None)

                if new_key == 'state_or_province':
                    logger.debug(f"Looking at state_province: {new_key}, {new_value}")
                    if new_value == "": 
                        key_to_remove.append((key, new_key))
                    else:
                       json_str = add_country_or_state("state_or_province.csv", json_str, key, new_key, new_value, country_temp)
                       
                 
    json_str = remove_keys_MineralSite(json_check=json_str, keys_list = key_to_remove)
    return json_str


def add_country_or_state(code_name, json_str, key, new_key, new_value, country):
    minmod_code = general.read_csv_to_dict(f"./codes/{code_name}")
    
    df = pd.DataFrame(minmod_code)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    
    json_str[key][new_key] = {}
    json_str[key][new_key]['normalized_uri'] = ""
    
    logger.info(f"Current: {json_str[key][new_key]}, new_key {new_key}")
 
        
    normalized_value = general.find_best_match(new_value, df['name'].tolist(), threshold=75)
    
    if normalized_value:
        logger.info(f"Normalized value {normalized_value}")
        result = df[df['name'] == normalized_value]
        m,_ = result.shape
        if m == 1:
             json_str[key][new_key]['normalized_uri'] = URL_STR + result['minmod_id'].values[0]
        else:
            new_result = result[result['country_name'] == country]
            if not new_result.empty: 
                json_str[key][new_key]['normalized_uri'] = URL_STR + new_result['minmod_id'].values[0]
            
    
    json_str[key][new_key] = general.add_extraction_dict(new_value, json_str[key][new_key])

    return json_str
    

def is_valid_point(s):
    ## used to check if there is anything besides numbers between the ()
    pattern = r"\w+\((-?\d+(\.\d+)?\s-?\d+(\.\d+)?)\)"
    match = re.search(pattern, s)
    
    # Return True if a match is found, False otherwise
    return match is not None

def remove_keys_MineralSite(json_check, keys_list):
    ## Removing any keys we don't need
    for outer_key, inner_key in keys_list:
        if inner_key is None:
            if outer_key in json_check:
                del json_check[outer_key]
        else:
            if outer_key in json_check and inner_key in json_check[outer_key]:
                del json_check[outer_key][inner_key]
    
    return json_check
