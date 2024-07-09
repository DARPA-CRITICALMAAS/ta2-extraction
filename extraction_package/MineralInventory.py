import warnings
import requests
import copy
import logging
from settings import CATEGORY_VALUES, SYSTEM_SOURCE, VERSION_NUMBER, URL_STR
import extraction_package.Prompts as prompts
import extraction_package.SchemaFormats as schemas
import extraction_package.AssistantFunctions as assistant
import extraction_package.GeneralFunctions as general


# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger("Inventory")



def create_mineral_inventory(thread_id, assistant_id, file_path, document_dict, commodity_list):
    
    commodities, correct_units = create_minmod_dict()
    
    # Get Tables
    ans = assistant.get_assistant_message(thread_id, assistant_id, prompts.find_relevant_table_instructions.replace("__COMMODITY__", str(commodity_list)))
    table_format = "{'Tables': ['Table 1 Name', 'Table 2 Name']}"
    relevant_tables = general.extract_json_strings(ans, table_format)
    
    logger.info(f" Here is the dictionary of relevant_tables: {relevant_tables} \n")
    
    ## return list of categories to extract then can decide which ones to run
    if relevant_tables is not None:
        categories_in_report = generate_categories(thread_id, assistant_id, relevant_tables)
        commodities_in_report = generate_commodities(thread_id, assistant_id, commodities, relevant_tables)
    else: categories_in_report, commodities_in_report = [], []
        
    commodities_in_report = clean_commodities(commodities_in_report, commodities)
    logger.info(f" List of idenitified Categories in the report: {categories_in_report} \n")
    logger.info(f" List of idenitified Commodities in the report: {commodities_in_report} \n")
    
    
    mineral_inventory_json = {"mineral_inventory":[]}
    done_first = False
    
    
    for commodity in commodities_in_report:
        
        inventory_format = schemas.create_inventory_format(commodities, commodity, document_dict)
        dictionary_format = schemas.create_mineral_extractions_format(commodity)
        
        ## Generating the actual mineral inventory
        for cat in CATEGORY_VALUES:
            extraction = None
            if cat in categories_in_report:
                logger.info(f" Extracting category: {cat} \n")
                extraction = extract_by_category(dictionary_format, cat, relevant_tables, thread_id, assistant_id, done_first)
                
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
            inner_commodity = {}
            inner_commodity['normalized_uri'] = URL_STR + commodities[commodity]
            inner_commodity = general.add_extraction_dict(commodity, inner_commodity)
            
            mineral_inventory_json["mineral_inventory"].append({"commodity": inner_commodity, "reference": {
                "document": document_dict}})
    
        
    logger.debug(f"Here is the mineral inventory json: \n {mineral_inventory_json}")
    
    return mineral_inventory_json

def clean_commodities(commodity_list, acceptable_commodities):
    final_list = []
    for comm in commodity_list:
        if comm in acceptable_commodities:
            final_list.append(comm)
            
    return final_list
    

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

def generate_commodities(thread_id, assistant_id, commodities, relevant_tables):
    
    ans = assistant.get_assistant_message(thread_id, assistant_id, 
    prompts.find_relevant_commodities.replace("__RELEVANT__", str(relevant_tables['Tables'])).replace("__ALLOWED_LIST__", str(commodities.keys()) )
    )
    commodities_format = "{'commodities': [value1, value2, ...]}"
    relevant_commodities = general.extract_json_strings(ans, commodities_format)
    
    if relevant_commodities is not None and 'commodities' in relevant_commodities:
        commodities_in_report = relevant_commodities["commodities"]
    else:
        commodities_in_report = []
    
    return commodities_in_report


def create_mineral_inventory_json(extraction_dict, inventory_format, unit_dict, file_path):
    output_str = {"mineral_inventory":[]}
    
    for inner_dict in extraction_dict['extractions']:
        current_inventory_format = copy.deepcopy(inventory_format)
    
        for key, value in inner_dict.items():
            logger.info(f"Checking the current_inventory_format: {key}: {value} \n")
            
            if not isinstance(value, str):
                value = str(value)
            
            if 'category' in key:
                current_inventory_format = check_category(current_inventory_format, URL_STR, value)
                
            elif 'zone' in key:
                ## cannot have an empty zone
                if value:
                    current_inventory_format['zone'] = value.lower()
                else: current_inventory_format.pop('zone')
                
            elif 'chemical' in key:
                current_inventory_format = check_material_form(current_inventory_format, URL_STR, value)
            
            elif 'cut' in key.lower() and 'unit' not in key.lower():
                current_inventory_format['cutoff_grade']['grade_value'] = value.lower()
                current_inventory_format['cutoff_grade'] = general.check_instance(current_extraction=current_inventory_format['cutoff_grade'], key = 'grade_value', instance=float)
                                       
            elif 'cut' in key.lower() and 'unit' in key.lower():
                current_inventory_format = check_cutoff_grade_unit(current_inventory_format, value, unit_dict)
             
            elif 'tonnage' in key.lower() and 'unit' not in key.lower():
                value = value.replace(",", "")
                current_inventory_format['ore']['ore_value'] = value.lower()
                current_inventory_format['ore'] = general.check_instance(current_extraction=current_inventory_format['ore'], key = 'ore_value', instance=float)
               
               
            elif 'tonnage' in key.lower() and 'unit' in key.lower():
                ## fix here to update to new form
                current_inventory_format = check_tonnage_unit(current_inventory_format, value, unit_dict)

            elif 'grade' in key.lower() and 'unit' in key.lower():
                logger.debug(f'grade unit value : {value}')
                if value == "":
                    current_inventory_format['grade'].pop('grade_unit')
                else:
                    ## need to fix this to new form as well
                    current_inventory_format['grade']['grade_unit'] = {}
                    current_inventory_format['grade']['grade_unit']['normalized_uri'] = ""
                    grade_unit_list = list(unit_dict.keys())
                    
                    if value == "%":
                        current_inventory_format['grade']['grade_unit']['normalized_uri'] = URL_STR + unit_dict['percent'] 
                        
                    else:
                        found_value = general.find_best_match(value, grade_unit_list) 
                        if found_value is not None:
                            current_inventory_format['grade']['grade_unit']['normalized_uri'] = URL_STR + unit_dict[found_value]           
                    logger.debug(f"Before add extraction_dict {current_inventory_format['grade']}")
                    current_inventory_format['grade']['grade_unit'] = general.add_extraction_dict(value, current_inventory_format['grade']['grade_unit'])
                    
                
                    
            elif 'grade' in key.lower() and 'unit' not in key.lower():
                current_inventory_format['grade']['grade_value'] = value.lower()
                current_inventory_format['grade'] = general.check_instance(current_extraction=current_inventory_format['grade'], key = 'grade_value', instance=float)
                
            
            elif 'table' in key.lower():
                output_page = general.find_correct_page(file_path=file_path, extractions = inner_dict)
                
                if output_page:
                    current_inventory_format['reference']['page_info'][0]['page'] = output_page
                else:
                    current_inventory_format['reference']['page_info'][0].pop('page')
                    
             
        current_inventory_format = check_empty_headers_add_contained_metal(current_inventory_format)        
        output_str["mineral_inventory"].append(current_inventory_format)
        
    return output_str




def check_cutoff_grade_unit(curr_json, value, unit_dict):
    ## need to change the method of doing this as well for doing the unit to follow new schema
    
    if value == "":
        curr_json['cutoff_grade'].pop('grade_unit')
        
    else:
        curr_json['cutoff_grade']['grade_unit'] = {}
        curr_json['cutoff_grade']['grade_unit']['normalized_uri'] = ""
        
        if value == '%':
            curr_json['cutoff_grade']['grade_unit']['normalized_uri'] = URL_STR + unit_dict['percent']
        
        elif value:
            grade_unit_list = list(unit_dict.keys())
            found_value = general.find_best_match(value, grade_unit_list[5:])

            if found_value is not None:
                # can check of the new new format
                curr_json['cutoff_grade']['grade_unit']['normalized_uri'] = URL_STR + unit_dict[found_value]
                
        curr_json['cutoff_grade']['grade_unit'] = general.add_extraction_dict(value, curr_json['cutoff_grade']['grade_unit'])
         
    return curr_json




def check_tonnage_unit(curr_json, value, unit_dict):
    kt_values = ["k","kt", "000s tonnes", "thousand tonnes", "thousands", "000s" , "000 tonnes", "ktonnes"]
    grade_unit_list = list(unit_dict.keys())
    curr_json['ore']['ore_unit'] = {}
    curr_json['ore']['ore_unit']['normalized_uri'] = ""
    
    if value == "":
        curr_json['ore'].pop('ore_unit')
    else:
        
        if value.lower() in kt_values:
                if curr_json['ore']['ore_value']: 
                    try:
                        float_val = float(curr_json['ore']['ore_value']) * 1000
                        curr_json['ore']['ore_value'] =  float_val
                        curr_json['ore']['ore_unit']['normalized_uri'] = URL_STR + unit_dict["tonnes"]
                        
                    except ValueError:
                        logger.error(f"Got Type Error for : {curr_json['ore']['ore_value']}")
                        
        else:
            found_value = general.find_best_match(value, grade_unit_list)
            if found_value is not None:
                logger.debug(f"Found match value for ore_unit {found_value}")
                curr_json['ore']['ore_unit']['normalized_uri'] = URL_STR + unit_dict[found_value.lower()]
        
        curr_json['ore']['ore_unit'] = general.add_extraction_dict(value, curr_json['ore']['ore_unit'])
            
                
    return curr_json

def check_category(current_json, URL_STR, value):
    ## update categories
    current_json['category'] = []
                     
    if value.lower() in CATEGORY_VALUES:
        if "+" in value.lower():
            new_vals = value.lower().split("+")
            for val in new_vals:
                current_json['category'].append(URL_STR + val.lower())
        else:
            current_json['category'].append(URL_STR + value.lower())
            
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
    # logger.debug(f"Starting extraction for check empty & add {extraction}")
    
    for key in keys_to_check:
        # logger.debug(f"Checking key {key} with values {extraction[key]}")
        if not extraction[key]:
            extraction.pop(key)
            # logger.debug("Currently this value is empty")
            
    
    if extraction.get("ore", None).get("ore_value", None):
        ore_value = extraction["ore"]["ore_value"]
    else: ore_value = None
    
    if extraction.get("grade", None).get("grade_value", None):
        grade_value = extraction["grade"]["grade_value"]
    else: grade_value = None 
    
    
    if  ore_value and grade_value:
        # logger.debug('We have ore_value and grade_value for contained_metal')
        try:
            extraction["contained_metal"] = round(ore_value*(grade_value/100), 4)
        except ValueError:
            logger.error(f"Get ValueError in check empty headers for ore_value: {ore_value} or grade_value {grade_value}")
            extraction.pop("contained_metal")
    else:
        # logger.debug("Didn't get ore_value")
        extraction.pop("contained_metal")
        
    # logger.debug(f"Here is the extraction post contained metal: {extraction}")
    return extraction


def extract_by_category(dictionary_format, curr_cat, relevant_tables, thread_id, assistant_id, done_first):
    if relevant_tables is not None and len(relevant_tables['Tables']) > 0:
      
        if not done_first:
            use_instructions = prompts.find_category_rows.replace("__RELEVANT__", str(relevant_tables)).replace("__CATEGORY__", curr_cat).replace("__DICTIONARY_FORMAT__", dictionary_format)
        else:
            use_instructions = prompts.find_additional_categories.replace("__RELEVANT__", str(relevant_tables)).replace("__CATEGORY__", curr_cat).replace("__DICTIONARY_FORMAT__", dictionary_format)
            
        ans = assistant.get_assistant_message(thread_id, assistant_id, use_instructions)

        extraction_dict = general.extract_json_strings(ans, dictionary_format, remove_comments = True)

        return extraction_dict

    else:
        return None

def check_material_form(curr_json, URL_STR, value):
    if not value:
        curr_json.pop('material_form')
        return curr_json
    
    curr_json['material_form'] = {"normalized_uri": ""}
    
    # print(f"Here is curr_json {curr_json}")
    material_form_picklist = general.read_csv_to_dict("./codes/material_form.csv")
    # print(f"material_form_picklist: {material_form_picklist}")
    
    options = {}
    for item in material_form_picklist:
        options[item['name']] = item['commodity_id']
        options[item['formula']] = item['commodity_id']
        
    found_value = general.find_best_match(value, list(options.keys()))
    if found_value is not None:
        logger.debug(f"Found match value for material_form {found_value}")
        curr_json['material_form']['normalized_uri'] = URL_STR + options[found_value.lower()]
        
    curr_json['material_form'] = general.add_extraction_dict(value, curr_json['material_form'])
    
    # print(f"Here is the curr_json in the file: {curr_json}")
    
    return curr_json
    
    
    
    