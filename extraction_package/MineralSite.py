import json
import warnings
import logging
import extraction_package.Prompts as prompts
import extraction_package.SchemaFormats as schemas
import extraction_package.AssistantFunctions as assistant
import extraction_package.GeneralFunctions as general
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger("Site") 

def create_document_reference(thread_id, assistant_id, url, title):
    # thread_id, assistant_id = assistant.create_assistant(file_path, commodity, sign)

    # thread_id, assistant_id = assistant.check_file(thread_id, assistant_id, file_path, commodity, sign)

    document_ref = schemas.created_document_ref(title, url)
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.name_instructions.replace('__DOCUMENT_REF___', document_ref))

    document_dict_temp = general.extract_json_strings(ans, document_ref)
    document_dict = clean_document_dict(document_dict_temp, title, url)
    doc_name = document_dict.get('title', '')   


    print(f" Here is the reference material for the document: \n {document_dict} \n")
    
    site_format = schemas.create_mineral_site(url, doc_name=doc_name)
    
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.loc_instructions.replace('__SITE_FORMAT__', site_format))
    
    mineral_site_json = general.extract_json_strings(ans, site_format)
    if mineral_site_json is None:
        mineral_site_json = json.loads(site_format)
        

    mineral_site_json = clean_mineral_site_json(mineral_site_json, title, url)

    print(f"Here is the Mineral Site Json: \n {mineral_site_json} \n")
    
    # assistant.delete_assistant(assistant_id)

    
        
    return document_dict, mineral_site_json

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
                if value and len(value.strip()) > 0 and value.strip()[0] == "[":
                    document_dict_temp[key] = [str(item.strip()).replace('"', "") for item in value[1:-1].split(',')]
                else:
                    document_dict_temp[key] = [str(item.strip()) for item in value.split(',')]  

    for key in key_to_remove:
        del document_dict_temp[key]

    return document_dict_temp
    

def clean_mineral_site_json(json_str, title, url):
    # cycle through dict
    key_to_remove = []

    for key, value in json_str.items():
        # print(f"Here is the key {key}, value {value}")
        if isinstance(value, str):
            if value.strip() == "" and key != "source_id" and key != "record_id":
                key_to_remove.append((key, None))  # Append a tuple (key, None) for outer keys
        if key == 'record_id':
            json_str[key] = "1"
        
        if key == 'name':
            json_str[key] = title
        if key == 'source_id':
            if value != url:
                json_str[key] = url
        if key == 'location_info' and isinstance(value, dict):
            for new_key, new_value in value.items():
                if new_key == 'crs':
                    json_str[key][new_key] = "EPSG:4326"
                    
                if new_key == 'location':
                    if isinstance(new_value, str) and (new_value.strip() == "" or new_value.strip() == "POINT()"):
                        key_to_remove.append((key, new_key))  # Append a tuple (key, new_key) for inner keys
                        key_to_remove.append((key, 'crs'))

    json_str = remove_keys_MineralSite(json_check=json_str, keys_list = key_to_remove)

    return json_str

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
