"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import os
import openai
import csv
import pandas as pd
import logging
import time

from first_pass import HelperFunctions, prompts 
from extraction_package import AssistantFunctions, GeneralFunctions
from settings import API_KEY


client = openai.OpenAI(api_key = API_KEY)
logger = logging.getLogger("GatherCommodities") 


def run(directory_path, csv_output_path):
    minmod_commodities = GeneralFunctions.read_csv_to_dict("./codes/minmod_commodities.csv")
    try:
        df = pd.read_csv(csv_output_path)
        names = df['File Name'].tolist()
    except FileNotFoundError:
        names = []  # Handle the case where the file is not found
    except pd.errors.EmptyDataError:
        names = []  # Handle the case where the file is empty or cannot be parsed by pandas
    except pd.errors.ParserError:
        names = [] 
        
    logger.info(f"Completed files {names}")
    
    commodities_list = []
    for key in minmod_commodities:
        commodities_list.append(key['CommodityinGeoKb'])

    
    file_list = [file_name for file_name in os.listdir(directory_path) if file_name.endswith('.pdf')]

    
    for idx, file_name in enumerate(file_list):
        record_id, file_title = file_name.split('_', 1)
        logger.info(f"Working on File: {file_title} file num: {idx+1} out of {len(file_list)}")
        
        if file_title not in names:
            
            file_path = directory_path + file_name
            
            file = client.files.create(
            file=open(f"{file_path}", "rb"),
            purpose='assistants'
            )

            thread_id, assistant_id = HelperFunctions.create_assistant_commodities(file.id)

            thread_id, assistant_id = HelperFunctions.check_file_commodities(thread_id, assistant_id, file_path, 0)
        
            if assistant_id is not None:
                ans = AssistantFunctions.get_assistant_message(thread_id, assistant_id, prompts.get_commodities_prompt.replace("__COMMODITIES_LIST__", str(commodities_list)))
                
                correct_format = {'commodities': ['commodity1', 'commodity2']}
                
                commodities_json = GeneralFunctions.extract_json_strings(ans, str(correct_format), remove_comments = False)
                
                if commodities_json == None:
                    commodities_json = correct_format
                    
                logger.info(f"Here are the extracted commodities: {commodities_json} \n")
                
                AssistantFunctions.delete_assistant(assistant_id)
                HelperFunctions.add_to_metadata(csv_output_path, file_title, record_id, commodities_json)
        else:
            logger.info("File was previously done \n")
        
###########################       parallelization      ############################

        
if __name__ == "__main__":
    t = time.time()
    comm = "earth_metals"
    download_dir = f"./reports/{comm}/"
    csv_output_path = f"./metadata/phase_one_{comm}_top10percent.csv"
    run(download_dir, csv_output_path)
    # print(f'Evaluation Took: {time.time()-t}')