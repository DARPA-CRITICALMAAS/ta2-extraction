"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import warnings
import logging
import requests
import old_extraction_package_v2.AssistantFunctions as assistant
import old_extraction_package_v2.MineralSite as site
import old_extraction_package_v2.GeneralFunctions as general
import old_extraction_package_v2.DepositTypes as deposits
import old_extraction_package_v2.SchemaFormats as schemas
import old_extraction_package_v2.ExtractPrompts as prompts
from settings import VERSION_NUMBER, SYSTEM_SOURCE
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger("Deposit")

def create_deposit_types(thread_id, assistant_id):
    logger.info(f"Getting started on deposit type")

    minmod_deposit_types = general.read_csv_to_dict("./codes/minmod_deposit_types.csv")
    deposit_id = {}
    for key in minmod_deposit_types:
        deposit_id[key['Deposit type']] = key['Minmod ID']
        
    
    deposit_format = schemas.create_deposit_format()
    
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, 
    prompts.deposit_instructions.replace('__DEPOSIT_FORMAT__', deposit_format))
    
    
    deposit_types_initial = general.extract_json_strings(ans, deposit_format)
    logger.info(f" Observed Deposit Types in the Report: \n {deposit_types_initial} \n")
    
    if deposit_types_initial is not None and len(deposit_types_initial['deposit_type']) > 0:
       
        deposit_format_correct = schemas.create_deposit_format_correct()
    
        ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.check_deposit_instructions.replace("__DEPOSIT_TYPE_LIST__", str(deposit_types_initial['deposit_type'])).replace("__DEPOSIT_ID__", str(deposit_id)).replace("__DEPOSIT_FORMAT_CORRECT__", deposit_format_correct)
        )
        
        deposit_types_output = general.extract_json_strings(ans, deposit_format_correct)
        
    else:
        deposit_types_output = {'deposit_type':[]}
        
    if deposit_types_output is None or len(deposit_types_output['deposit_type']) == 0:
        deposit_types_json = {'deposit_type_candidate':[]}
    else:
        deposit_types_json = format_deposit_candidates(deposit_types_output) 
        
    logger.info(f" Final Formatted Deposit Type: {deposit_types_json} \n")
    
    # assistant.delete_assistant(assistant_id)
        
    return deposit_types_json


def format_deposit_candidates(deposit_list):
    deposit_type_candidate = { "deposit_type_candidate": []}
    
    for dep in deposit_list['deposit_type']:
        inner_dict = {}
        inner_dict["observed_name"] = dep
        if dep in deposit_list['deposit_type']:
            inner_dict["normalized_uri"] = deposit_list['deposit_type'][dep]
        else:
            inner_dict.pop("normalized_uri")
            
        inner_dict["source"] =  SYSTEM_SOURCE + " "+ VERSION_NUMBER
        inner_dict["confidence"] = 1/len(deposit_list['deposit_type']) 
        deposit_type_candidate['deposit_type_candidate'].append(inner_dict)
    
        if inner_dict['normalized_uri'] == "":
            inner_dict.pop('normalized_uri')
        
    return deposit_type_candidate