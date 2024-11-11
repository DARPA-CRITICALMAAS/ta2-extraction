"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import json
import warnings
import re
import csv
import PyPDF2
from pyzotero import zotero
import os
import requests
from fuzzywuzzy import process
from settings import LIBRARY_ID, LIBRARY_TYPE, SYSTEM_SOURCE, VERSION_NUMBER, CDR_BEARER 
from old_extraction_package_v2.ExtractPrompts import *
import old_extraction_package_v2.AssistantFunctions as assistant
import logging

# Get logger
logger = logging.getLogger("GeneralFunctions")

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')


def download_document(doc_id):
    url = f'https://api.cdr.land/v1/docs/documents//v1/docs/document/{doc_id}'
    headers = {
        'accept': 'application/json',
        'Authorization': CDR_BEARER
    }

    url_meta = f'https://api.cdr.land/v1/docs/documents//v1/docs/document/meta/{doc_id}'

    # Send the initial GET request
    response = requests.get(url_meta, headers=headers)

    if response.status_code == 200:
        # Save the response content to a file
        resp_json = json.loads(response.content)
        title = resp_json['title']
        response = requests.get(url, headers=headers)

        if response.status_code == 200:    
            with open(f'./{title}.pdf', 'wb') as file:
                file.write(response.content)
        logger.info(f"Document downloaded and saved as '{title}.pdf'")
    else:
        logger.error(f"Failed to download document. Status code: {response.status_code}")
        logger.error(f"Response content: {response.content}")

def append_section_to_JSON(file_path, header_name, whole_section):
    logger.debug(f"Writing {header_name}")
    
    json_schema = {"MineralSite": whole_section}
    logger.debug(f"Json Schema before write: {json_schema}")
    with open(file_path, "w") as json_file:
        json.dump(convert_int_or_float(json_schema), json_file, indent=2)

    # Writing to a file using json.dump with custom serialization function
    

def check_JSON_exists(file_name):
    data = { "MineralSite": []}
    if not os.path.exists(file_name):
        # If the file doesn't exist, create an empty object
        with open(file_name, 'w') as json_file:
            json.dump(data, json_file)
        logger.info(f"Created {file_name}")
    else:
        # open what was already created
        with open(file_name, "r") as json_file:
            data = json.load(json_file)
    
    return data

def extract_json_strings(input_string, correct_format, remove_comments = False):
    start = input_string.find('{')
    if start != -1:
        # Remove comments starting with // or # since we get a lot in the return
        if remove_comments: 
            input_string = re.sub(r'(?<!["\'])//.*?\n|/\*.*?\*/|(#.*?\n)', '', input_string)
        
        count = 0
        for i in range(start, len(input_string)):
            if input_string[i] == '{':
                count += 1
            elif input_string[i] == '}':
                count -= 1
            if count == 0:
                json_str = input_string[start:i+1]
                # logger.debug(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    # here is the error, lets fix this
                    logger.error(f"JSON error for checking the format: {e}")
                    return assistant.fix_formats(json_str, correct_format)       
    else:
        return None

    
def read_csv_to_dict(file_path):
    data_dict_list = []
    
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            data_dict_list.append(dict(row))
    
    return data_dict_list

def is_array(s):
    return s.startswith('[') and s.endswith(']')


def find_best_match(input_str, list_to_match, threshold=75):
    # Get the best match and its score
    best_match, score = process.extractOne(input_str, list_to_match)

    # Check if the score is above the threshold
    if score >= threshold:
        return best_match
    else:
        return None
    
def find_correct_page(file_path, extractions):
    ## get a series of strings to look at to find these values in curr_json
    ## probably ask Goran how many strings should be looked at
    # logger.debug(f"This is the inner_dict: {extractions}, {type(extractions)}")
    page = []
    target_strings = []
    for key, value in extractions.items():
        if len(value) > 0 and len(target_strings) < 3:
            target_strings.append(value)
            
    
    logger.debug(f"Target strings found: {target_strings}")
    ## DO TWO METHODS: METHOD 1
    # checks based off first target for the second ones
    
    if len(target_strings) > 2:
        logger.debug(f"Before search_text_in_pdf {file_path}")
        table_pages = search_text_in_pdf(file_path, target_strings[0])
        matching_pages = {}
        logger.debug(f"Here are table_pages: {table_pages}")
        for string in target_strings[1:]:
            matching_pages[string] = string_in_page(file_path, string, table_pages)
            if len(list(matching_pages.values())) > 0: 
                page = find_common_numbers(matching_pages)
    
        logger.debug(f"Matching pages: {matching_pages}")
        logger.debug(f"Output pages: {page}")


    if len(page) == 0:
        return page
    else:
        return int(page[0])
                
              
def string_in_page(pdf_path, target_string, check_pages):
    page_numbers = []
    # Open the PDF file in binary mode
    if not check_pages:
        return page_numbers

    with open(pdf_path, 'rb') as file:
        
        # Create a PDF reader
        pdf = PyPDF2.PdfReader(file)
        
        # Iterate over each page
        for page_num in check_pages:
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_new = ' '.join(text.replace("\t", " ").split()).lower()
            # Check if target string is in the page's text
            if target_string.lower() in text_new:
                page_numbers.append(page_num)      
                      
    return page_numbers

def search_text_in_pdf(pdf_path, target_string):
    page_numbers = []

    # Open the PDF file in binary mode
    logger.debug("before opening path")
    with open(pdf_path, 'rb') as file:
        
        logger.debug("opened path")
        # Create a PDF reader
        try:
            pdf = PyPDF2.PdfReader(file)
        except PyPDF2.utils.PdfReadError as e:
            logger.error(f"PyPDF2 read error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        
        # logger.debug("PYPDF2 ERROR")
        # Iterate over each page
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_new = ' '.join(text.replace("\t", " ").split()).lower()
            # Check if target string is in the page's text
            if target_string.lower() in text_new:
                page_numbers.append(page_num)  
    
    logger.debug(f"returning page numbers: {page_numbers}")   
    return page_numbers

def find_common_numbers(dictionary):

    number_lists = list(dictionary.values())

    common_numbers = set(number_lists[0]).intersection(*number_lists[1:])

    return list(common_numbers)


def check_instance(current_extraction, key, instance):
    # logger.debug(f"Previous value: {current_extraction[key]}")
    output_value = None
    
    if key in current_extraction:
        curr_value = current_extraction[key]
        logger.debug(f"Looking at key {key} : {curr_value}")
        
        ## want to test the current value or if its 0
        if isinstance(curr_value, str) and len(curr_value) == 0:
            ## in case we have an empty value should pop that value out
            logger.debug("The value is empty")
            output_value = None
        
        elif instance == float and isinstance(curr_value, str):
            # if its a float we want to change the string to the correct float value
            logger.debug(f"Original value: {curr_value} \n")
            
            curr_value = current_extraction[key]
            numeric_chars = re.findall(r'[\d.]+', curr_value)
            str_value = ''.join(numeric_chars)
        
            try:
                output_value = float(str_value)
                logger.debug(f"Updated value: {output_value}")
                
            except ValueError:
                logger.error(f"Get value error for {curr_value} instance {instance} \n")
                
        
        elif isinstance(curr_value, instance):
            # if it is the correct instance type
            logger.debug(f"MATCH: curr_value {curr_value} instance {instance} \n")
            if instance == list and len(current_extraction[key]) == 0:
                output_value = None
            else:
                output_value = current_extraction[key]
        else:
            try:
            # testing the current value as the instance
                output_value = instance(curr_value)
        
            except ValueError:
                logger.error(f"Get value error for {curr_value} instance {instance} \n")
    
    if output_value is None:
        current_extraction.pop(key)
    else:
        current_extraction[key] = output_value
    
    
    logger.debug(f"check_instance: Final cleaned instance {current_extraction} \n")
    return current_extraction

# def get_zotero(url):
   
#     zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, ZOLTERO_KEY)
#     file_list = url.split("/")
#     file_key = file_list[-1]
#     try:
#         file_item = zot.item(file_key)
#         title = file_item['data']['title']
#     except Exception:
#         logger.error(f'Error connectiong to Zotero. Missing Title')
#         title = ""
    
#     # print(f"Zoltero Information: file_key {file_key} Title: {title} \n")
#     return title


def add_extraction_dict(value, inner_json):
    logger.debug(f"In the inner dict function: {inner_json}")
    if not inner_json['normalized_uri']:
        inner_json.pop('normalized_uri')
        
        
    inner_json['observed_name'] = value
    inner_json['confidence'] = 1 
    inner_json['source'] = SYSTEM_SOURCE + " " + VERSION_NUMBER  
    logger.debug(f"after extraction_dict: {inner_json}")
    return inner_json


def convert_int_or_float(obj):
    if isinstance(obj, dict):
        return {key: convert_int_or_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_int_or_float(item) for item in obj]
    elif isinstance(obj, (int, float)):
        return obj
    elif isinstance(obj, str) and obj.isdigit():
        return int(obj)
    elif isinstance(obj, str) and obj.replace('.', '', 1).isdigit():
        return float(obj)
    return obj