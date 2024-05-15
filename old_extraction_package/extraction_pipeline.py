import openai
import json
import os
import warnings
import time
import requests
import concurrent.futures
import multiprocessing
import argparse
from datetime import datetime
from settings import API_KEY 
from old_extraction_package.extraction_functions import *
from old_extraction_package.schema_formats import *
from old_extraction_package.prompts import *

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

client = openai.OpenAI(api_key = API_KEY)

def create_document_reference(file_path, url, commodity, sign, title):
    thread_id, assistant_id = create_assistant(file_path, commodity, sign)

    thread_id, assistant_id = check_file(thread_id, assistant_id, file_path, commodity, sign)

    document_ref = created_document_ref(title, url)

    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions= name_instructions.replace('__DOCUMENT_REF___', document_ref)
    )
    
    get_completed_assistant_run(thread_id, run.id)
    ans = get_assistant_message(thread_id, run.id)

    document_dict_temp = extract_json_strings(ans, document_ref)
    document_dict = clean_document_dict(document_dict_temp, title, url)
    # doc_month = document_dict.get('month', '')  
    # doc_year = document_dict.get('year', '')   
    doc_name = document_dict.get('title', '')   

    # if doc_year and doc_month:
    #     doc_date = f"{doc_year}-{doc_month}"
    # else:
    #     doc_date = ''

    print(f" Here is the reference material for the document: \n {document_dict} \n")
    
    site_format = create_mineral_site(url, doc_name=doc_name)
    
    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions=loc_instructions.replace('__SITE_FORMAT__', site_format)
    )
    get_completed_assistant_run(thread_id, run.id)
    ans = get_assistant_message(thread_id, run.id)
    
    mineral_site_json = extract_json_strings(ans, site_format)
    if mineral_site_json is None:
        mineral_site_json = json.loads(site_format)
        

    mineral_site_json = clean_mineral_site_json(mineral_site_json, title, url)

    print(f"Here is the Mineral Site Json: \n {mineral_site_json} \n")
    
    resp_code = delete_assistant(assistant_id)

    if resp_code == 200:
        print(f" Deleted assistant for Document Reference \n")
    else:
        print(f" Deletion FAILED for Document Reference \n")
        
    return document_dict, mineral_site_json

def create_deposit_types(file_path, url, commodity, sign, title):
  
    thread_id, assistant_id =create_assistant(file_path, commodity, sign)
    
    thread_id, assistant_id = check_file(thread_id, assistant_id, file_path, commodity, sign)
    
    minmod_deposit_types = read_csv_to_dict("./codes/minmod_deposit_types.csv")
    deposit_id = {}
    for key in minmod_deposit_types:
        deposit_id[key['Deposit type']] = key['Minmod ID']
        
    
    deposit_format = create_deposit_format()
    
    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions=deposit_instructions.replace('__COMMODITY__', commodity).replace('__DEPOSIT_FORMAT__', deposit_format)
    )

    get_completed_assistant_run(thread_id, run.id)
    ans = get_assistant_message(thread_id, run.id)
    
    deposit_types_initial = extract_json_strings(ans, deposit_format)
    print(f" Observed Deposit Types in the Report: \n {deposit_types_initial} \n")
    
    if deposit_types_initial is not None and len(deposit_types_initial['deposit_type']) > 0:
        # print("Creating the run")
        deposit_format_correct = create_deposit_format_correct()
        run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=check_deposit_instructions.replace("__DEPOSIT_TYPE_LIST__", str(deposit_types_initial['deposit_type'])).replace("__DEPOSIT_ID__", str(deposit_id)).replace("__DEPOSIT_FORMAT_CORRECT__", deposit_format_correct).replace("__COMMODITY__", commodity)
        )
        
        get_completed_assistant_run(thread_id, run.id)
        ans = get_assistant_message(thread_id, run.id)
        deposit_types_output = extract_json_strings(ans, deposit_format_correct)
        
    else:
        deposit_types_output = {'deposit_type':[]}
        
    if deposit_types_output is None or len(deposit_types_output['deposit_type']) == 0:
        deposit_types_json = {'deposit_type_candidate':[]}
    else:
        deposit_types_json = format_deposit_candidates(deposit_types_output) 
        
    print(f" Final Formatted Deposit Type: {deposit_types_json} \n")
    
    resp_code = delete_assistant(assistant_id)

    if resp_code == 200:
        print(f" Deleted assistant for Deposit Types \n")
    else:
        print(f" Deletion for Deposit Types FAILED \n")
    
    return deposit_types_json

def create_mineral_inventory(document_dict, file_path, url, commodity, sign, title):
   
    thread_id, assistant_id = create_assistant(file_path, commodity, sign)
    
    thread_id, assistant_id = check_file(thread_id, assistant_id,file_path, commodity, sign)
    
    minmod_commodities = read_csv_to_dict("./codes/minmod_commodities.csv")
    commodities = {}
    for key in minmod_commodities:
        commodities[key['CommodityinGeoKb']] = key['minmod_id']
        
    minmod_units = read_csv_to_dict("./codes/minmod_units.csv")
    correct_units = {}
    for key in minmod_units:
        correct_units[key['unit name']] = key['minmod_id']
        correct_units[key['unit aliases']] = key['minmod_id']
    

    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions=find_relevant_table_instructions.replace("__COMMODITY__", commodity)
    )

    get_completed_assistant_run(thread_id, run.id)
    ans = get_assistant_message(thread_id, run.id)
    
    table_format = "{'Tables': ['Table 1 Name', 'Table 2 Name']}"
    relevant_tables = extract_json_strings(ans, table_format)
    
    
    print(f" Here is the dictionary of relevant_tables: {relevant_tables} \n")
    
    ## return list of categories to extract then can decide which ones to run
    if relevant_tables is not None:
        # print("Creating the thread")
        run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=find_relevant_categories.replace("__RELEVANT__", str(relevant_tables['Tables']))
        )
        get_completed_assistant_run(thread_id, run.id)
        ans = get_assistant_message(thread_id, run.id)
        
        categories_format = "{'categories': [value1, value2, ...]}"
        relevant_cats = extract_json_strings(ans, categories_format)
        
        if relevant_cats is not None:
            categories_in_report = relevant_cats["categories"]
        else:
            categories_in_report = []
    else:
        categories_in_report = []
        
    print(f" List of idenitified Categories in the report: {categories_in_report} \n")
    mineral_inventory_json = {"mineral_inventory":[]}
    done_first = False
    
    categories_to_test = ["INFERRED", "INDICATED","INDICATED+INFERRED","MEASURED","MEASURED+INDICATED",
                         "MEASURED+INFERRED","PROBABLE","PROVEN","PROVEN+PROBABLE"]
    
    doc_month = document_dict.get('month', '')
    doc_year = document_dict.get('year', '')
    if doc_month and doc_year:
        doc_date = f"{doc_year}-{doc_month}"
    else: 
        doc_date = ''
        
    inventory_format = create_inventory_format(commodities, commodity, document_dict, doc_date)
    
    if doc_date == '':
        inventory_format.pop('date')
    
    dictionary_format = create_mineral_extractions_format(commodity)
    
    for cat in categories_to_test:
        extraction = None
        if cat.lower() in categories_in_report:
            print(f" Extracting category: {cat} \n")
            extraction = extract_by_category(commodity, sign, dictionary_format, cat, relevant_tables, thread_id, assistant_id, done_first)
            
            print(f" Extracted: {extraction} \n")
            
            if extraction is not None and 'extractions' in extraction:
                
                cleaned = create_mineral_inventory_json(extraction, inventory_format, correct_units, file_path)
                mineral_inventory_json["mineral_inventory"] += cleaned['mineral_inventory']
            
        if not done_first:
            done_first = True
            

    if len(mineral_inventory_json["mineral_inventory"]) == 0:
        mineral_inventory_json["mineral_inventory"].append({"commodity": "https://minmod.isi.edu/resource/" + commodities[commodity], "reference": {
            "document": document_dict}})
        
        
    resp_code = delete_assistant(assistant_id)

    if resp_code == 200:
        print(f" Deleted assistant for Mineral Inventory \n")
    else:
        print(f" Deletion FAILED for Mineral Inventory \n")
        
    return mineral_inventory_json

########################## parallelization ##################################################

def document_parallel_extract(
    pdf_paths,
    file_names,
    url_list,
    primary_commodity,
    element_sign,
    output_path
    ):

    pdf_paths = [pdf_paths]*len(file_names)
    primary_commodity = [primary_commodity]*len(file_names)
    element_sign = [element_sign]*len(file_names)
    output_path = [output_path]*len(file_names)
    print(f"Running the parallelization method with {len(file_names)} files \n")
    delete_all_files()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:

        list(executor.map(run, pdf_paths, file_names, url_list, primary_commodity, element_sign, output_path))



def run(folder_path, file_name, url, commodity, sign, output_folder_path):
    t = time.time()
    file_path = folder_path + file_name
    title = get_zotero(url)
    
    print(f"Working on file: {folder_path+file_name} title: {title} url: {url} commodity of interest is {commodity} \n")
    
    
    document_dict, mineral_site_json = create_document_reference(file_path, url, commodity.lower(), sign, title)

    deposit_types_json = create_deposit_types(file_path, url, commodity.lower(), sign, title)
    
    mineral_inventory_json = create_mineral_inventory(document_dict, file_path, url, commodity.lower(), sign, title)
    
    mineral_site_json["MineralSite"][0]['mineral_inventory'] = mineral_inventory_json['mineral_inventory']
    mineral_site_json["MineralSite"][0]['deposit_type_candidate'] = deposit_types_json['deposit_type_candidate']
    print(f" mineral site json :\n {mineral_site_json} \n")
    current_datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    

    new_name = file_name[:-4].replace(" ", "_")

    output_file_path = f'{output_folder_path}{new_name}_summary_{current_datetime_str}.json'


    # Writing to a file using json.dump with custom serialization function
    with open(output_file_path, "w") as json_file:
        json.dump(convert_int_or_float(mineral_site_json), json_file, indent=2)
        
    print(f"Combined data written to {output_file_path} Took {time.time()-t} s \n")
    


    
    
if __name__ == "__main__":
    print("Running the extraction pipeline for file: Provide the Folder path, File Name, Zotero URL \n\n")
    delete_all_files()
    
    
    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--pdf_p', type=str, help='Path to the reports folder', required=True)
    parser.add_argument('--pdf_name', type=str, help='The name of the document', required=True)
    parser.add_argument('--primary_commodity', type=str, help='Primary commodity we are interested in', required=True)
    parser.add_argument('--element_sign', type=str, help='The element sign of the primery commodity', required=True)
    parser.add_argument('--url', type=str, help='The Zotero URL required to fullfile the DOI portion', required=True)
    parser.add_argument('--output_path', type=str, help='Path where you want the output saved', required=True)
    
    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    pdf_p = args.pdf_p
    pdf_name = args.pdf_name
    primary_commodity = args.primary_commodity
    element_sign = args.element_sign
    zotero_url = args.url
    output_folder_path = args.output_path
    
    print(f"Current Inputs: file_path: {pdf_p+pdf_name} zotero_url: {zotero_url} \n")
    run(pdf_p, pdf_name, zotero_url, primary_commodity, element_sign, output_folder_path)
    

    
    





    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        
    

