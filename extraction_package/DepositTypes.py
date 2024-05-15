import warnings
import logging
import requests
import extraction_package.AssistantFunctions as assistant
import extraction_package.MineralSite as site
import extraction_package.GeneralFunctions as general
import extraction_package.DepositTypes as deposits
import extraction_package.SchemaFormats as schemas
import extraction_package.Prompts as prompts
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger("Deposit")

def create_deposit_types(thread_id, assistant_id, commodity):
  
    # thread_id, assistant_id = assistant.create_assistant(file_path, commodity, sign)
    # thread_id, assistant_id = assistant.check_file(thread_id, assistant_id, file_path, commodity, sign)
    

    minmod_deposit_types = general.read_csv_to_dict("./codes/minmod_deposit_types.csv")
    deposit_id = {}
    for key in minmod_deposit_types:
        deposit_id[key['Deposit type']] = key['Minmod ID']
        
    
    deposit_format = schemas.create_deposit_format()
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, 
    prompts.deposit_instructions.replace('__COMMODITY__', commodity).replace('__DEPOSIT_FORMAT__', deposit_format))
    
    
    deposit_types_initial = general.extract_json_strings(ans, deposit_format)
    logger.info(f" Observed Deposit Types in the Report: \n {deposit_types_initial} \n")
    
    if deposit_types_initial is not None and len(deposit_types_initial['deposit_type']) > 0:
       
        deposit_format_correct = schemas.create_deposit_format_correct()
    
        ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.check_deposit_instructions.replace("__DEPOSIT_TYPE_LIST__", str(deposit_types_initial['deposit_type'])).replace("__DEPOSIT_ID__", str(deposit_id)).replace("__DEPOSIT_FORMAT_CORRECT__", deposit_format_correct).replace("__COMMODITY__", commodity)
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
        inner_dict["normalized_uri"] = deposit_list['deposit_type'][dep]
        inner_dict["source"] = "report" 
        inner_dict["confidence"] = 1/len(deposit_list['deposit_type']) 
        deposit_type_candidate['deposit_type_candidate'].append(inner_dict)
        
    return deposit_type_candidate