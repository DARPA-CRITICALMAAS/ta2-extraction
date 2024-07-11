first_pass_instructions = """You are a geology expert and you are very good in understanding mining reports. 
You will be given a text from a mining report and a table name. From this mining report, you will need to 
extract all of the commodities that are mentioned and are relevant.
"""

get_commodities_prompt = """Given this document, can you return all commodities that are referenced in the 
Mineral Reserve Estimates or Mineral Resource Estimates. The commodities MUST be in this list 
__COMMODITIES_LIST__. Return the found commodities in this JSON format 
{{'commodities': [commodity_1, commodity_2,....]}}. If there are no commodities found, return 
{{'commodities': []}}.
"""

file_instructions = """If the file was correctly uploaded and can be read return YES otherwise return NO. 
                        Only return the Yes or No answer."""