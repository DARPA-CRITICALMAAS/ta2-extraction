import os
import openai
import csv
from first_pass import HelperFunctions, prompts 
from extraction_package import AssistantFunctions, GeneralFunctions
from settings import API_KEY


client = openai.OpenAI(api_key = API_KEY)


def run(directory_path, csv_output_path):
    minmod_commodities = GeneralFunctions.read_csv_to_dict("./codes/minmod_commodities.csv")
    
    commodities_list = []
    for key in minmod_commodities:
        commodities_list.append(key['CommodityinGeoKb'])

    
    file_list = [file_name for file_name in os.listdir(directory_path) if file_name.endswith('.pdf')]

    for idx, file_name in enumerate(file_list):
        print(f"Working on File: {file_name} file num: {idx+1} out of {len(file_list)}")
        file_path = directory_path + file_name
        
        file = client.files.create(
        file=open(f"{file_path}", "rb"),
        purpose='assistants'
        )

        thread_id, assistant_id = HelperFunctions.create_assistant_commodities(file.id)

        thread_id, assistant_id = HelperFunctions.check_file_commodities(thread_id, assistant_id, file_path)
      
        
        ans = AssistantFunctions.get_assistant_message(thread_id, run.id, prompts.get_commodities_prompt.replace("__COMMODITIES_LIST__", str(commodities_list)))
        
        correct_format = {'commodities': []}
        
        commodities_json = GeneralFunctions.extract_json_strings(ans, str(correct_format), remove_comments = False)
        
        if commodities_json == None:
            commodities_json = correct_format
            
        print(f"Here are the extracted commodities: {commodities_json}")
        
        AssistantFunctions.delete_assistant(assistant_id)
        HelperFunctions.add_to_metadata(csv_output_path, file_name, commodities_json)
        
if __name__ == "__main__":
    directory_path = './reports/zinc/completed/'
    csv_output_path = './commodities_metadata_zinc.csv'

    run(directory_path, csv_output_path)