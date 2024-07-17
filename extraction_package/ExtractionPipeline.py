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
import shutil
import re

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
    commodity_list,
    output_path
    ):

    pdf_paths = [pdf_paths]*len(file_names)
    output_path = [output_path]*len(file_names)
    
    logger.debug(f"Running the parallelization method with {len(file_names)} files \n")
    assistant.delete_all_files()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(run, pdf_paths, file_names, commodity_list, output_path))



## new structure where we try the run again while we don't get errors
def run(folder_path, file_name, commodity_list, output_folder_path):
    ## this is where we keep running if we get any errors
    
    t = time.time()
    
    file_path = folder_path + file_name
    
    thread_id, assistant_id, message_file_id = assistant.create_assistant(file_path)
    thread_id, assistant_id, message_file_id = assistant.check_file(thread_id, assistant_id, message_file_id, file_path)
    try:
        pipeline(thread_id, assistant_id, message_file_id, folder_path, file_name, commodity_list, output_folder_path)
        assistant.delete_assistant(assistant_id=assistant_id) 
        logger.info("Moved file to completed folder \n")
    except Exception as e:
        logger.error(f"{file_name} : Pipeline Error: {e} \n")
        assistant.delete_assistant(assistant_id=assistant_id)
        logger.error(f"Rerunning: {file_name} \n")
        
        ## here need to move file to partial complete vs full complete
        
        # return run(folder_path, file_name, commodity, sign, output_folder_path)
    
    logger.info(f"Entire run takes: {time.time()-t} \n\n")
    
    
def pipeline(thread_id, assistant_id, message_file_id, folder_path, file_name, commodity_list, output_folder_path ):
    file_path = folder_path + file_name
    site_completed, inventory_completed, deposit_completed = False, False, False
    record_id, title = file_name.split('_', 1)
    
    
    logger.info(f"Working on file: {file_name} title: {title} commodities to extract {commodity_list} \n")
    new_name = re.sub(r'[()\[\]"\']', '', file_name)
    new_name = new_name[:-4].replace(" ", "_")
    
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
        document_dict, mineral_site_json = site.create_document_reference(thread_id, assistant_id, record_id, title)
        logger.debug(f"Document dict Output: {document_dict} \n Mineral Site Output: {mineral_site_json} \n")
        
        inner_data = [mineral_site_json]
        logger.debug(f"Inner_data after the mineral site json {inner_data} \n")
        general.append_section_to_JSON(output_file_path, "MineralSite", inner_data)


        inner_data[0]['mineral_inventory'] = { "reference": {"document": document_dict}}
        general.append_section_to_JSON(output_file_path, "reference", inner_data)
        logger.debug(f"Outputed inner_data after adding reference & mineral inventory: {inner_data} \n")
        site_completed = True
    else:
        inner_list = inner_data[0].get('mineral_inventory', None)
        if isinstance(inner_list, list) and len(inner_list) > 0:
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
        
        ## here loop through: ask again or just get the important table first then loop through?
        
        ## can do something here to check the multiple commodities. Even a for loop works for now. Need To update
        ## by adding each value. Pass through after the first pass within the larger meta data.
        thread_id = assistant.create_new_thread(message_file_id=message_file_id, 
                        content=prompts.content.replace("__FOCUS__", "the mineral inventory"))

        mineral_inventory_json = inventory.create_mineral_inventory(thread_id, assistant_id,file_path,document_dict, commodity_list)
        mineral_inventory_json = inventory.post_process(mineral_inventory_json)
        logger.debug(f"Finished mineral inventory after post processing: {mineral_inventory_json} \n")
        
        
        if inner_data[0].get("mineral_inventory", None):
            inner_data[0]['mineral_inventory'] = mineral_inventory_json['mineral_inventory']
            general.append_section_to_JSON(output_file_path, "MineralInventory", inner_data)
            inventory_completed = True
            
    else: inventory_completed = True
        
    
    if "deposit_type_candidate" not in inner_data[0]:
        logger.debug("NO deposit Type so need to add")
        thread_id = assistant.create_new_thread(message_file_id=message_file_id, 
                        content=prompts.content.replace("__FOCUS__", "mineral deposit types"))
        
        ## Need to check if we need to add more versions of this.
        deposit_types_json = deposits.create_deposit_types(thread_id, assistant_id)
        logger.debug(f"Output deposit types: {deposit_types_json} \n")
        inner_data[0]['deposit_type_candidate'] = deposit_types_json['deposit_type_candidate']
        general.append_section_to_JSON(output_file_path, "Deposit types", inner_data)
        deposit_completed = True
        
    else: deposit_completed = True
        
    
    if site_completed and inventory_completed and deposit_completed:
        logger.debug(f"ALL Sections data written to {output_file_path} \n")
        shutil.move(output_file_path, f'{output_folder_path}completed/{new_name}_summary_{current_datetime_str}.json' )
    else: 
        raise FilesNotCompleted()
        
        

    



if __name__ == "__main__":
    logger.info("Running the extraction pipeline for file: Provide the Folder path, File Name, Zotero URL \n")
    
    assistant.delete_all_files()


    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--pdf_p', type=str, help='Path to the reports folder', required=True)
    parser.add_argument('--pdf_name', type=str, help='The name of the document', required=True)
    parser.add_argument('--commodity_list', type=str, help='Primary commodity we are interested in', required=True)
    parser.add_argument('--output_path', type=str, help='Path where you want the output saved', required=True)

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    folder_path = args.pdf_p
    file_name = args.pdf_name.split(",")
    commodity_list = args.primary_commodity
    output_folder_path = args.output_path
    
    logger.info(f"Current Inputs: file_path: {file_name} \n")
    run(folder_path, file_name, commodity_list, output_folder_path)
   
