from extraction_package.schema_formats import *

instructions = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a text from a mining report and a table name. You have to find out what are the different combinations of
classification (which is either indicated, inferred, measure, proven, probable, or total ), cut-off (represented as a decimal), tonnage (in Tonnes) and 
grade (given in %) from the given table in the text. Please extract the name of the element and place it in the output below without any additional text
Note we only care about the mineral __COMMODITY__ represented by __SIGN__"
"""

name_instructions = f"""Please tell me description information about the attached document such as the title, 
list of author names (ignore professional titles), year and month it was published as integers, and a one sentence description. 
Note that the authors can be identified by key words such as authors or prepared by and can be found in the first few pages of the document.
Return the response as a JSON structure that follows this format __DOCUMENT_REF___. Only return the JSON structure.
Any unknown values should be returned as ""
"""

loc_instructions = f"""Find the geographic location of the mining 
site in the document and put it in geographic coordinates using latitude and longitude that will then be converted to
geometry point structure using WGS84 standard. If there are multiple points the format will look like: 
"MULTIPOINT(long1 lat1,long2 lat2, ..)". If there is no location information or if the correct conversions cannot be made replace the value as empty strings. 
Fill out the JSON structure Mineral Site based on the geographic information found.
Here is an example format: Mineral Site: __SITE_FORMAT__.
Return only the filled in MineralSite Json Structure with the given keys and found values. Do not 
add any additional comments and do not use // within the JSON structure. Only return one Json structure.
"""

deposit_instructions = f"""Identify the deposit types from the attached document. Note that the main
commodity in this paper is __COMMODITY__.The output was to be formatted in the JSON structure Deposit_Type
__DEPOSIT_FORMAT__.  Please return the filled in Deposit_Type JSON Structure or 
leave the list empty if there are No matching deposit types. Return only the JSON structure.
"""
check_deposit_instructions = f"""Given this list with deposit type observed texts __DEPOSIT_TYPES_LIST__ and with the main commodity being __COMMODITY__, 
check that each deposit is in the acceptable list of deposits or there is a deposit type that appears to be close. Update the 
deposit type with the correct ID from this given list __DEPOSIT_ID__ or return an empty string if a match can't be made. The return format
should only be the JSON structure: __DEPOSIT_FORMAT_CORRECT__ where in the value deposit_id is changed to the correct ID and the https url is still included.
The keys of the return should be all the values given in deposit types JSON structure given.
Do not return any additional comments and do not use // in the JSON structure.
"""


find_relevant_table_instructions = f"""
Can you go through the document, find every table that discusses the mineral resource estimates or mineral reserve estimates. If there are multiple resource
or reserve tables pull the tables that are closest to the doc_date. Avoid any resource sensitivities tables. 
Return the list of tables as a JSON structure: {{"Tables": ["Table 1 Name","Table 2 Name",...]}}. 
Only return the JSON structure. Note that these tables are typically found in the Mineral resource or Mineral
reserve sections of the document. These tables should have column names that describe categories, tonnage, 
cut off grade, or grades related to the commodity __COMMODITY__.
If there are no tables just return None.
"""
 
find_relevant_categories = f""" From this list of tables: __RELEVANT__, return the JSON structure that
contains the list of categories found in the tables. The allotted categories are ["inferred", "indicated","measured", 
"probable", "proven", "proven+probable", "inferred+indicated", "inferred+measured", "measured+indicated"]. The output should be a
JSON that follow this format : {{"categories": [value1, value2, ...]}} and each value should be all
lower case.
"""

find_category_rows = f""" From this list of tables: __RELEVANT__, create a python dictionary that
captures all rows that describe __COMMODITY__ resource or reserve estimate data. Each 
relevant row should have the category __CATEGORY__. The rows should also include the following headers.
Zone: the named area where the resources were extracted from (Note: Do not include any Total values).
__MINERAL_SIGN__ Cut-Off: The threshold grade used to determine the economic viability of 
mining the __COMMODITY__ resource (this might not be provided in some tables). 
__MINERAL_SIGN__ Cut-Off Unit: The unit that is labeled cut off and always start from the smallest cut-off value. Note if it is a NSR value. 
__MINERAL_SIGN__ Tonnage: The calculated or estimated tonnage for the resource. 
__MINERAL_SIGN__ Tonnage Unit: The unit that the tonnage was presented in, which should be in tonnes, thousand tonnes, 
million tonnes, or gram per tonne. 
__MINERAL_SIGN__ Grade %: The concentration of __COMMODITY__ in the resource, which should 
be converted into a percentage. 
Also return what tables the rows were extracted from. If any values are unknown return it as an empty string ''

Return the information as dictionary with an internal list of keys and values, wrapped in "", that follows this
format: __DICTIONARY_FORMAT__. Do not add any additional comments using // in the returned dictionary format.
"""

find_additional_categories = f""" Follow the same instructions as the previous extraction for tables __RELEVANT__
but extract for rows that relate to the category, __CATEGORY__. Return the information as dictionary with an internal list of keys and values, wrapped in "", that follows this
format:  __DICTIONARY_FORMAT__. Do not add any additional comments using // in the returned dictionary format. If any values are unknown make sure to
return them as empty strings.

Note if no rows are found for __CATEGORY__ do not return any JSON.
"""

JSON_format_fix = """ Given this incorrectly formatted JSON, correct the JSON to follow this schema __CORRECT_SCHEMA__
and return the correctly formatted JSON. Here is the incorrectly formatted JSON: __INCORRECT__
"""