import warnings
import time
import concurrent.futures
import argparse
import sys
import logging
import logging.config
from datetime import datetime
import extraction_package.AssistantFunctions as assistant
import extraction_package.MineralSite as site
import extraction_package.Prompts as prompts
import extraction_package.GeneralFunctions as general
import extraction_package.DepositTypes as deposits
import extraction_package.MineralInventory as inventory

class FilesNotCompleted(Exception):
    pass

## ADD LOGGING
logging.config.fileConfig(fname='config.ini', disable_existing_loggers=True)

# Get the logger specified in the file
logger = logging.getLogger("Pipeline")

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

## ask if we want to do this in a class method/not storing or if it should be a series
## of functions


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
    
    logger.debug(f"Running the parallelization method with {len(file_names)} files \n")
    assistant.delete_all_files()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(run, pdf_paths, file_names, url_list, primary_commodity, element_sign, output_path))



## new structure where we try the run again while we don't get errors
def run(folder_path, file_name, url, commodity, sign, output_folder_path):
    ## this is where we keep running if we get any errors
    
    t = time.time()
    
    file_path = folder_path + file_name
    
    thread_id, assistant_id, message_file_id = assistant.create_assistant(file_path, commodity, sign)
    thread_id, assistant_id, message_file_id = assistant.check_file(thread_id, assistant_id, message_file_id, file_path, commodity, sign)
    try:
        pipeline(thread_id, assistant_id, message_file_id, folder_path, file_name, url, commodity, sign, output_folder_path)
        assistant.delete_assistant(assistant_id=assistant_id)
    except Exception as e:
        logger.error(f"{file_name} : Pipeline Error: {e}")
        assistant.delete_assistant(assistant_id=assistant_id)
        logger.error(f"Rerunning: {file_name}")
        return run(folder_path, file_name, url, commodity, sign, output_folder_path)
    
    logger.info(f"Entire run takes: {time.time()-t}")
    
    
def pipeline(thread_id, assistant_id, message_file_id, folder_path, file_name, url, commodity, sign, output_folder_path ):
    file_path = folder_path + file_name
    site_completed, inventory_completed, deposit_completed = False, False, False
    title = general.get_zotero(url)
    
    logger.info(f"Working on file: {file_name} title: {title} url: {url} commodity of interest is {commodity} \n")
    new_name = file_name[:-4].replace(" ", "_")
    
    current_datetime_str = datetime.now().strftime("%Y%m%d")
    output_file_path = f'{output_folder_path}{new_name}_summary_{current_datetime_str}.json'
    
    ## Get the JSON 
    data = general.check_JSON_exists(output_file_path)
    logger.debug(f"JSON form filepath: {data} \n\n")
    inner_data, inner_list = data.get("MineralSite"), {}
    logger.debug(f"Inner data from checking JSON: {inner_data} \n")
   
   # do a check that its there
    if not inner_data:
        logger.debug("No Mineral_site or document_dict \n")
        document_dict, mineral_site_json = site.create_document_reference(thread_id, assistant_id, url, title)
        logger.debug(f"Document dict Output: {document_dict} \n Mineral Site Output: {mineral_site_json} \n")
        
        inner_data.append(mineral_site_json)
        logger.debug(f"Inner_data after the mineral site json {inner_data} \n")
        general.append_section_to_JSON(output_file_path, "MineralSite", inner_data)

        reference = {"mineral_inventory":{ "reference": {"document": document_dict}}}
        inner_data.append(reference)
        general.append_section_to_JSON(output_file_path, "reference", inner_data)
        logger.debug(f"Outputed inner_data after adding reference & mineral inventory: {inner_data} \n")
        site_completed = True
    else:
        inner_list = inner_data[1].get('mineral_inventory', None)
        if isinstance(inner_list, list):
            # means that we have mineral inventory
            document_dict = inner_list[0].get('reference', None).get('document', None)
        else:
            document_dict = inner_list.get('reference', None).get('document', None)
        site_completed = True
       
        
    logger.debug(f"Here is the doc_dict: {document_dict} \n ")
    logger.debug(f"Before going to Mineral Inventory the inner list: {inner_list} \n")
    
    ## type dict if mineral inventory not made, list when it is has correct mineral inventory
    if isinstance(inner_list, dict):
        logger.debug("No commodity in mineral inventory \n")
        thread_id = assistant.create_new_thread(message_file_id=message_file_id, 
                        content=prompts.content.replace("__FOCUS__", "the mineral inventory"))

        mineral_inventory_json = inventory.create_mineral_inventory(thread_id, assistant_id,file_path,document_dict, commodity.lower(), sign)
        
        if inner_data[1].get("mineral_inventory", None):
            inner_data.pop(1)
            inner_data.append(mineral_inventory_json)
            general.append_section_to_JSON(output_file_path, "MineralInventory", inner_data)
            inventory_completed = True
            
    else: inventory_completed = True
        
    
    if len(inner_data) < 3:
        logger.debug("NO deposit Type so need to add")
        thread_id = assistant.create_new_thread(message_file_id=message_file_id, 
                        content=prompts.content.replace("__FOCUS__", "mineral deposit types"))
        deposit_types_json = deposits.create_deposit_types(thread_id, assistant_id,  commodity.lower())
        logger.debug(f"Output deposit types: {deposit_types_json} \n")
        inner_data.append(deposit_types_json)
        general.append_section_to_JSON(output_file_path, "Deposit types", inner_data)
        deposit_completed = True
        
    else: deposit_completed = True
        
    
    if site_completed and inventory_completed and deposit_completed:
        logger.debug(f"ALL Sections data written to {output_file_path} \n")
    else: 
        raise FilesNotCompleted()
        
        

    



if __name__ == "__main__":
    logger.info("Running the extraction pipeline for file: Provide the Folder path, File Name, Zotero URL \n")
    
    assistant.delete_all_files()


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
    
    logger.info(f"Current Inputs: file_path: {pdf_p+pdf_name} zotero_url: {zotero_url} \n")
    run(pdf_p, pdf_name, zotero_url, primary_commodity, element_sign, output_folder_path)
   
