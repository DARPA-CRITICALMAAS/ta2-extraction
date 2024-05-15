import warnings
import requests
import copy
import logging
from settings import CATEGORY_VALUES
import extraction_package.Prompts as prompts
import extraction_package.SchemaFormats as schemas
import extraction_package.AssistantFunctions as assistant
import extraction_package.GeneralFunctions as general

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger("Inventory")
url_str = "https://minmod.isi.edu/resource/"


def create_mineral_inventory(thread_id, assistant_id, file_path, document_dict, url, commodity, sign, title):
   
    # thread_id, assistant_id = create_assistant(file_path, commodity, sign)
    # thread_id, assistant_id = check_file(thread_id, assistant_id,file_path, commodity, sign)
    
    commodities, correct_units = create_minmod_dict()
    
    # Get Tables
    ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.find_relevant_table_instructions.replace("__COMMODITY__", commodity))
    table_format = "{'Tables': ['Table 1 Name', 'Table 2 Name']}"
    relevant_tables = general.extract_json_strings(ans, table_format)
    
    logger.info(f" Here is the dictionary of relevant_tables: {relevant_tables} \n")
    
    ## return list of categories to extract then can decide which ones to run
    if relevant_tables is not None:
        categories_in_report = generate_categories(thread_id, assistant_id, relevant_tables)
    else: categories_in_report = []
        
        
    logger.info(f" List of idenitified Categories in the report: {categories_in_report} \n")
    mineral_inventory_json = {"mineral_inventory":[]}
    done_first = False
    
    
    
    inventory_format = schemas.create_inventory_format(commodities, commodity, document_dict)
    dictionary_format = schemas.create_mineral_extractions_format(commodity)
    
    ## Generating the actual mineral inventory
    for cat in CATEGORY_VALUES:
        extraction = None
        if cat in categories_in_report:
            logger.info(f" Extracting category: {cat} \n")
            extraction = extract_by_category(commodity, sign, dictionary_format, cat, relevant_tables, thread_id, assistant_id, done_first)
            
            logger.info(f" Extracted: {extraction} \n")
            
            if extraction is not None and extraction.get('extractions'):
                new_extraction = {}
                new_extraction['extractions'] = [entry for entry in extraction['extractions'] if any(entry.values())]
                logger.debug(f'Cleaned Up extraction of any full empty values: {new_extraction} \n')
                
                cleaned = create_mineral_inventory_json(new_extraction, inventory_format, correct_units, file_path)
                mineral_inventory_json["mineral_inventory"] += cleaned['mineral_inventory']
            
        if not done_first:
            done_first = True
            

    if len(mineral_inventory_json["mineral_inventory"]) == 0:
        mineral_inventory_json["mineral_inventory"].append({"commodity": "https://minmod.isi.edu/resource/" + commodities[commodity], "reference": {
            "document": document_dict}})
        
    return mineral_inventory_json

def generate_categories(thread_id, assistant_id, relevant_tables):
    ans = assistant.get_assistant_message(thread_id, assistant_id, 
    prompts.find_relevant_categories.replace("__RELEVANT__", str(relevant_tables['Tables']))
    )
    categories_format = "{'categories': [value1, value2, ...]}"
    relevant_cats = general.extract_json_strings(ans, categories_format)
    
    if relevant_cats is not None:
        categories_in_report = relevant_cats["categories"]
    else:
        categories_in_report = []
    
    return categories_in_report


def create_mineral_inventory_json(extraction_dict, inventory_format, unit_dict, file_path):
    output_str = {"mineral_inventory":[]}
    ## add conversion to tonnes
    
    for inner_dict in extraction_dict['extractions']:
        current_inventory_format = copy.deepcopy(inventory_format)
    
        for key, value in inner_dict.items():
            logger.info(f"Checking the current_inventory_format:{key}: {value} \n")
            
            if isinstance(value, int) or isinstance(value, float):
                value = str(value)
            
            elif 'category' in key:
                current_inventory_format = check_category(current_inventory_format, url_str, value)
            
            elif 'zone' in key:
                current_inventory_format['zone'] = value.lower()
                
            elif 'cut' in key.lower() and 'unit' not in key.lower():
                current_inventory_format['cutoff_grade']['grade_value'] = value.lower()
                current_inventory_format['cutoff_grade'] = general.check_instance(current_extraction=current_inventory_format['cutoff_grade'], key = 'grade_value', instance=float)
                                       
            elif 'cut' in key.lower() and 'unit' in key.lower():
                if value == '%':
                    current_inventory_format['cutoff_grade']['grade_unit'] = url_str + unit_dict['percent']
                
                elif value:
                    grade_unit_list = list(unit_dict.keys())
                    found_value = general.find_best_match(value, grade_unit_list[5:])
       
                    if found_value is not None:
                        current_inventory_format['cutoff_grade']['grade_unit'] = url_str + unit_dict[found_value]
                        
                logger.debug(f"Error lets see current_inventory_format: {current_inventory_format} \n")
                current_inventory_format['cutoff_grade'] = general.check_instance(current_extraction=current_inventory_format['cutoff_grade'], key = 'grade_unit', instance=str)
                     
            elif 'tonnage' in key.lower() and 'unit' not in key.lower():
                value = value.replace(",", "")
                current_inventory_format['ore']['ore_value'] = value.lower()
                current_inventory_format['ore'] = general.check_instance(current_extraction=current_inventory_format['ore'], key = 'ore_value', instance=float)
                
               
            elif 'tonnage' in key.lower() and 'unit' in key.lower():
                current_inventory_format = check_tonnage(current_inventory_format, value, unit_dict)
                current_inventory_format['ore'] = general.check_instance(current_extraction=current_inventory_format['ore'], key = 'ore_unit', instance=str)
                
                
            elif 'grade' in key.lower():
                current_inventory_format['grade']['grade_unit'] = url_str + unit_dict['percent']
                current_inventory_format['grade']['grade_value'] = value.lower()
                
                current_inventory_format['grade'] = general.check_instance(current_extraction=current_inventory_format['grade'], key = 'grade_value', instance=float)
                
                if not 'grade_value' in current_inventory_format['grade']:
                    current_inventory_format['grade'].pop('grade_value')
                
            elif 'table' in key.lower():
                output_page = general.find_correct_page(file_path=file_path, extractions = inner_dict)
                
                if output_page:
                    current_inventory_format['reference']['page_info'][0]['page'] = output_page
                else:
                    current_inventory_format['reference']['page_info'][0].pop('page')
                
             
        current_inventory_format = check_empty_headers_add_contained_metal(current_inventory_format)        
        output_str["mineral_inventory"].append(current_inventory_format)
        
    return output_str


def check_tonnage(curr_json, value, unit_dict):
    kt_values = ["k","kt", "000s tonnes", "thousand tonnes", "thousands", "000s" , "000 tonnes", "ktonnes"]
    grade_unit_list = list(unit_dict.keys())
    
    if value.lower() in kt_values:
            if curr_json['ore']['ore_value']: 
                try:
                    float_val = float(curr_json['ore']['ore_value']) * 1000
                    curr_json['ore']['ore_value'] =  float_val
                    curr_json['ore']['ore_unit'] = url_str + unit_dict["tonnes"]
                except ValueError:
                    logger.error(f"Got Type Error for : {curr_json['ore']['ore_value']}")
                    
    else:
        found_value = general.find_best_match(value, grade_unit_list)
        if found_value is not None:
            logger.debug(f"Found match value for ore_unit {found_value}")
            curr_json['ore']['ore_unit'] = url_str + unit_dict[found_value.lower()]
    
    return curr_json

def check_category(current_json, url_str, value):
    ## update categories
    current_json['category'] = []
                     
    if value.lower() in CATEGORY_VALUES:
        if "+" in value.lower():
            new_vals = value.lower().split("+")
            for val in new_vals:
                current_json['category'].append(url_str + val.lower())
        else:
            current_json['category'].append(url_str + value.lower())
            
    current_json = general.check_instance(current_extraction=current_json, key = 'category', instance=list)
    return current_json

def create_minmod_dict():
    minmod_commodities = general.read_csv_to_dict("./codes/minmod_commodities.csv")
    commodities = {}
    for key in minmod_commodities:
        commodities[key['CommodityinGeoKb']] = key['minmod_id']
        
    minmod_units = general.read_csv_to_dict("./codes/minmod_units.csv")
    correct_units = {}
    for key in minmod_units:
        correct_units[key['unit name']] = key['minmod_id']
        correct_units[key['unit aliases']] = key['minmod_id']

    return commodities, correct_units


def check_empty_headers_add_contained_metal(extraction):
    keys_to_check = ["ore", "grade", "cutoff_grade"]
    logger.debug(extraction)
    
    for key in keys_to_check:
        if not extraction[key]:
            extraction.pop(key)
            logger.debug("Currently this value is empty")
    
    if "ore" in extraction and "ore_value" in extraction["ore"]:
        ore_value = extraction["ore"]["ore_value"]
    else: ore_value = None
    
    if "grade" in extraction and "grade_value" in extraction["ore"]:
        grade_value = extraction["grade"]["grade_value"]
    else: grade_value = None 
    
    if  ore_value and grade_value:
        try:
            extraction["contained_metal"] = round(ore_value*(grade_value/100), 4)
        except ValueError:
            logger.error(f"Get ValueError in check empty headers for ore_value: {ore_value} or grade_value {grade_value}")
            extraction.pop("contained_metal")
    else:
        extraction.pop("contained_metal")

    return extraction


def extract_by_category(commodity, commodity_sign, dictionary_format, curr_cat, relevant_tables, thread_id, assistant_id, done_first):
    if relevant_tables is not None and len(relevant_tables['Tables']) > 0:
      
        if not done_first:
            use_instructions = prompts.find_category_rows.replace("__RELEVANT__", str(relevant_tables)).replace("__CATEGORY__", curr_cat).replace("__COMMODITY__", commodity).replace("__MINERAL_SIGN__", commodity_sign).replace("__DICTIONARY_FORMAT__", dictionary_format)
        else:
            use_instructions = prompts.find_additional_categories.replace("__RELEVANT__", str(relevant_tables)).replace("__CATEGORY__", curr_cat).replace("__DICTIONARY_FORMAT__", dictionary_format)
            
        ans = assistant.get_assistant_message(thread_id, assistant_id, use_instructions)

        extraction_dict = general.extract_json_strings(ans, dictionary_format, remove_comments = True)

        return extraction_dict

    else:
        return None
