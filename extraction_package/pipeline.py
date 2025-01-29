"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""


"""
 This File is the Extraction Pipeline. The goal will to take a pdf File and fill out the necessary portions of that make up an extraction and will do any normalizations
 to that data that is needed. The three major portions are the Mineral Reference, Mineral Inventory, and Deposit Types. 

"""

import warnings
import time
import concurrent.futures
import argparse
import logging
import logging.config
import re
import warnings
import time
import concurrent.futures
import argparse
import sys
import logging
import logging.config
from datetime import datetime, timezone
import time
import warnings
import requests
import json
import shutil
import extraction_package.LLMFunctions as LLMfunc
import extraction_package.genericFunctions as generic
import extraction_package.documentRefHelp as docRef
import extraction_package.mineralInventoryHelp as inventory
import extraction_package.depositTypesHelp as deposit

import re
import statistics

class FilesNotCompleted(Exception):
    pass



# Get the logger specified in the file
logger = logging.getLogger(__name__)

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

## ask if we want to do this in a class method/not storing or if it should be a series
## of functions


def document_parallel_extract(
    pdf_paths,
    file_names,
    output_path
    ):

    pdf_paths = [pdf_paths]*len(file_names)
    output_path = [output_path]*len(file_names)
    
    logger.debug(f"Running the parallelization method with {len(file_names)} files \n")
   
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(run, pdf_paths, file_names, output_path))



## new structure where we try the run again while we don't get errors
def run(folder_path, file_name, output_folder_path):
    ## this is where we keep running if we get any errors
    
    t = time.time()

    try:
        output = pipeline(folder_path, file_name, output_folder_path)
        return output
    except Exception as e:
        logger.error(f"{file_name} : Pipeline Error: {e} \n")
        logger.error(f"Rerunning: {file_name} \n")
        return None
    logger.info(f"Entire run takes: {time.time()-t} \n\n")
    
    
def pipeline(folder_path, file_name, output_folder_path):
    file_path = folder_path + file_name
    record_id, title = file_name.split('_', 1)
    
    
    logger.info(f"Working on file: {title} \n")
    new_name = record_id
    
    output_file_path = f'{output_folder_path}{new_name}.json'
    
    ## Get the JSON 
    table_pages, deposit_pages, TOC_pages = LLMfunc.get_pages_with_tables(file_path)
    
    logger.debug(f"Ran the Page Classifer: table pages: {table_pages} deposit pages {deposit_pages} TOC pages {TOC_pages}")
   
        
    ## here is where we will create the document_dict & mineral_site_json
    document_dict, mineral_site_json = docRef.extractDocRefandMineralSite(TOC_pages, file_path, record_id, title)
    
        
    logger.debug(f"Document dict Output: {document_dict} \n Mineral Site Output: {mineral_site_json} \n")
    
    full_json = [mineral_site_json]
    logger.debug(f"full_json after the mineral site json {full_json} \n")
    logger.debug(f"Here is the output_file_path: {output_file_path}")
    generic.append_section_to_JSON(output_file_path, "MineralSite", full_json)

    ## initiating the extraction
    full_json[0]['mineral_inventory'] = []
    full_json[0]['deposit_type_candidate'] = []
    full_json[0]['modified_at'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    full_json[0]['created_by'] = "https://minmod.isi.edu/users/s/inferlink"
    full_json[0]['reference'] = [{"document":document_dict}]
    generic.append_section_to_JSON(output_file_path, "reference", full_json)
    logger.debug(f"Outputed full_json after adding reference & mineral inventory: {full_json} \n")
       
    logger.debug(f"Here is the doc_dict: {document_dict} \n ")
    
    
   
    mineral_inventory_json = inventory.create_mineral_inventory(file_path, document_dict, table_pages)
    mineral_inventory_json = inventory.post_process(mineral_inventory_json)
    full_json[0]['mineral_inventory'] = mineral_inventory_json['mineral_inventory']
    logger.debug(f"Finished mineral inventory after post processing: {mineral_inventory_json} \n")
    
    
    
    generic.append_section_to_JSON(output_file_path, "MineralInventory", full_json)
    
    
    deposit_types_json = deposit.create_deposit_types(file_path, deposit_pages)

    
    full_json[0]['deposit_type_candidate'] = deposit_types_json['deposit_type_candidate']
    logger.debug(f"Outputing this value: {full_json}")
    generic.append_section_to_JSON(output_file_path, "Deposit types", full_json)
    
    # add the created by and modified at time
    


    logger.debug(f"ALL Sections data written to {output_file_path} \n")
    # shutil.move(output_file_path, f'{output_folder_path}completed/{new_name}_summary_{current_datetime_str}.json' )
    return full_json
        


if __name__ == "__main__":
    logger.info("Running the extraction pipeline for file: Provide the Folder path, File Name, Zotero URL \n")
    

    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--pdf_p', type=str, help='Path to the reports folder', required=True)
    parser.add_argument('--pdf_name', type=str, help='The name of the document', required=True)
    parser.add_argument('--output_path', type=str, help='Path where you want the output saved', required=True)

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    folder_path = args.pdf_p
    file_name = args.pdf_name
    output_folder_path = args.output_path
    
    logger.info(f"Current Inputs: file_path: {file_name} \n")
    run(folder_path, file_name, output_folder_path)
   
