import openai
import json
import os
import warnings
import requests
import concurrent.futures
import multiprocessing
import argparse
from datetime import datetime
from settings import API_KEY 
from extraction_package.extraction_functions import *
from extraction_package.schema_formats import *
from extraction_package.prompts import *

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

client = openai.OpenAI(api_key = API_KEY)

def create_document_reference():
    file = client.files.create(
    file=open(f"{os.environ.get('file_path')}", "rb"),
    purpose='assistants'
    )

    thread_id, assistant_id = create_assistant(file.id)

    thread_id, assistant_id = check_file(thread_id, assistant_id)

    document_ref = created_document_ref(os.environ.get('title'), os.environ.get('url'))

    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions= name_instructions.replace('__DOCUMENT_REF___', document_ref)
    )
  
    ans = get_assistant_response(thread_id, run.id)

    document_dict_temp = extract_json_strings(ans, document_ref)
    document_dict = clean_document_dict(document_dict_temp)
    doc_month = document_dict['month']
    doc_year = document_dict['year']
    doc_name = document_dict['title']
    doc_date = f"{doc_year}-{doc_month}"

    print(f"{os.environ.get('file_path')}: Here is the reference material for the document: \n {document_dict} \n")
    
    site_format = create_mineral_site(os.environ.get('url'), doc_name=doc_name)
    
    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions=loc_instructions.replace('__SITE_FORMAT__', site_format)
    )
    ans = get_assistant_response(thread_id, run.id)
    
    mineral_site_json = extract_json_strings(ans, site_format)
    if mineral_site_json is None:
        mineral_site_json = json.loads(site_format)
        

    mineral_site_json = clean_mineral_site_json(mineral_site_json)

    print(f"{os.environ.get('file_path')} Here is the Mineral Site Json: \n {mineral_site_json} \n")
    
    resp_code = delete_assistant(assistant_id)

    if resp_code == 200:
        print(f"{os.environ.get('file_path')} Deleted assistant for Document Reference \n")
    else:
        print(f"{os.environ.get('file_path')} Deletion FAILED for Document Reference \n")
        
    return document_dict, mineral_site_json

def create_deposit_types():
    file = client.files.create(
    file=open(f"{os.environ.get('file_path')}", "rb"),
    purpose='assistants'
    )
    thread_id, assistant_id =create_assistant(file.id)
    
    thread_id, assistant_id = check_file(thread_id, assistant_id)
    
    minmod_deposit_types = read_csv_to_dict("./codes/minmod_deposit_types.csv")
    deposit_id = {}
    for key in minmod_deposit_types:
        deposit_id[key['Deposit type']] = key['Minmod ID']
        
    
    deposit_format = create_deposit_format()
    
    run = client.beta.threads.runs.create(
    thread_id=thread_id,
        
    assistant_id=assistant_id,
    instructions=deposit_instructions.replace('__COMMODITY__', os.environ.get('commodity')).replace('__DEPOSIT_FORMAT__', deposit_format)
    )

    ans = get_assistant_response(thread_id, run.id)
    deposit_types_initial = extract_json_strings(ans, deposit_format)
    print(f"{os.environ.get('file_path')} Observed Deposit Types in the Report: \n {deposit_types_initial} \n")
    
    if deposit_types_initial is not None and len(deposit_types_initial['deposit_type']) > 0:
        # print("Creating the run")
        deposit_format_correct = create_deposit_format_correct()
        run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=check_deposit_instructions.replace("__DEPOSIT_TYPE_LIST__", str(deposit_types_initial['deposit_type'])).replace("__DEPOSIT_ID__", str(deposit_id)).replace("__DEPOSIT_FORMAT_CORRECT__", deposit_format_correct).replace("__COMMODITY__", os.environ.get('commodity'))
        )
        
        
        ans = get_assistant_response(thread_id, run.id)
        deposit_types_output = extract_json_strings(ans, deposit_format_correct)
    else:
        deposit_types_output = {'deposit_type':[]}
        
    if len(deposit_types_output['deposit_type']) == 0:
        deposit_types_json = {'deposit_type_candidate':[]}
    else:
        deposit_types_json = format_deposit_candidates(deposit_types_output) 
        
    print(f"{os.environ.get('file_path')} Final Formatted Deposit Type: {deposit_types_json} \n")
    
    resp_code = delete_assistant(assistant_id)

    if resp_code == 200:
        print(f"{os.environ.get('file_path')} Deleted assistant for Deposit Types \n")
    else:
        print(f"{os.environ.get('file_path')} Deletion for Deposit Types FAILED \n")
    
    return deposit_types_json

def create_mineral_inventory(document_dict):
    file = client.files.create(
    file=open(f"{os.environ.get('file_path')}", "rb"),
    purpose='assistants'
    )
    thread_id, assistant_id = create_assistant(file.id)
    
    thread_id, assistant_id = check_file(thread_id, assistant_id)
    
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
    instructions=find_relevant_table_instructions
    )

    ans = get_assistant_response(thread_id, run.id)
    table_format = "{'Tables': {'Table 1 Name': page_number,'Table 2 Name': page_number}"
    relevant_tables = extract_json_strings(ans, table_format)
    
    print(f"{os.environ.get('file_path')} Here is the dictionary of relevant_tables: {relevant_tables} \n")
    
    ## return list of categories to extract then can decide which ones to run
    if relevant_tables is not None:
        # print("Creating the thread")
        run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=find_relevant_categories.replace("__RELEVANT__", str(relevant_tables['Tables'].keys()))
        )
        ans = get_assistant_response(thread_id, run.id)
        categories_format = "{'categories': [value1, value2, ...]}"
        relevant_cats = extract_json_strings(ans, categories_format)
        
        if relevant_cats is not None:
            categories_in_report = relevant_cats["categories"]
        else:
            categories_in_report = []
    else:
        categories_in_report = []
        
    print(f"{os.environ.get('file_path')} List of idenitified Categories in the report: {categories_in_report} \n")
    mineral_inventory_json = {"MineralInventory":[]}
    done_first = False
    
    categories_to_test = ["INFERRED", "INDICATED","INDICATED+INFERRED","MEASURED","MEASURED+INDICATED",
                         "MEASURED+INFERRED","PROBABLE","PROVEN","PROVEN+PROBABLE"]
    
    doc_month = document_dict['month']
    doc_year = document_dict['year']
    doc_date = f"{doc_year}-{doc_month}"
    inventory_format = create_inventory_format(commodities, os.environ.get('commodity'), document_dict, doc_date)
    dictionary_format = create_mineral_extractions_format(os.environ.get("commodity"))
    
    for cat in categories_to_test:
        extraction = None
        if cat.lower() in categories_in_report:
            print(f"{os.environ.get('file_path')} Extracting category: {cat} \n")
            extraction = extract_by_category(os.environ.get("commodity"), os.environ.get("sign"), dictionary_format, cat, relevant_tables, thread_id, assistant_id, done_first)
            print(f"{os.environ.get('file_path')} Extracted: {extraction} \n")
            
        if extraction is not None or cat.lower() in categories_in_report:
            cleaned = create_mineral_inventory_json(extraction, inventory_format, relevant_tables, correct_units)
            mineral_inventory_json["MineralInventory"] += cleaned['MineralInventory']
            
        if not done_first:
            done_first = True
            
    reference = {"reference": {
            "document": document_dict}}

    if len(mineral_inventory_json["MineralInventory"]) == 0:
        mineral_inventory_json["MineralInventory"].append({"commodity": "https://minmod.isi.edu/resource/" + commodities[os.environ.get('commodity')]})
        mineral_inventory_json["MineralInventory"].append(reference)
        
    resp_code = delete_assistant(assistant_id)

    if resp_code == 200:
        print(f"{os.environ.get('file_path')} Deleted assistant for Mineral Inventory \n")
    else:
        print(f"{os.environ.get('file_path')} Deletion FAILED for Mineral Inventory \n")
        
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

    with concurrent.futures.ThreadPoolExecutor() as executor:

        results = list(executor.map(run, pdf_paths, file_names, url_list, primary_commodity, element_sign, output_path))

    return results


def run(folder_path, file_name, url, commodity, sign, output_folder_path):
    
    print(f"Working on file: {file_name} url: {url} commodity of interest is {commodity} \n")
    os.environ['url'] = url
    os.environ['commodity'] = commodity.lower()
    os.environ['sign'] = sign
    os.environ['file_path'] = folder_path + file_name
    os.environ['title'] = get_zotero(os.environ.get('url'))
    
    
    document_dict, mineral_site_json = create_document_reference()

    deposit_types_json = create_deposit_types()
    
    mineral_inventory_json = create_mineral_inventory(document_dict)
    
    mineral_site_json["MineralSite"][0]['MineralInventory'] = mineral_inventory_json['MineralInventory']
    mineral_site_json["MineralSite"][0]['deposit_type_candidate'] = deposit_types_json['deposit_type_candidate']
    print(f"{os.environ.get('file_path')} mineral site json :\n {mineral_site_json} \n")
    current_datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    

    new_name = file_name[:-4].replace(" ", "_")

    output_file_path = f'{output_folder_path}{new_name}_summary_{current_datetime_str}.json'


    # Writing to a file using json.dump with custom serialization function
    with open(output_file_path, "w") as json_file:
        json.dump(convert_int_or_float(mineral_site_json), json_file, indent=2)
        
    print(f"Combined data written to {output_file_path} \n")
    


    
    
if __name__ == "__main__":
    print("Running the extraction pipeline for file: Provide the Folder path, File Name, Zotero URL \n\n")
    
    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--pdf_p', type=str, help='Path to the reports folder', required=True)
    parser.add_argument('--pdf_name', type=str, help='The name of the document', required=True)
    parser.add_argument('--primary_commodity', type=str, help='Primary commodity we are interested in', required=True)
    parser.add_argument('--element_sign', type=str, help='The element sign of the primery commodity', required=True)
    parser.add_argument('--url', type=str, help='The Zotero URL required to fullfile the DOI portion', required=True)

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    pdf_p = args.pdf_p
    pdf_name = args.pdf_name
    primary_commodity = args.primary_commodity
    element_sign = args.element_sign
    zotero_url = args.url
    
    print(f"Current Inputs: file_path: {pdf_p+pdf_name} zotero_url: {zotero_url} \n")
    run(pdf_p, pdf_name, zotero_url, primary_commodity, element_sign)
    

    
    





    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        
    

