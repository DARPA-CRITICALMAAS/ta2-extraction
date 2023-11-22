import time
import json
import warnings
import ast
import sys
import os
from datetime import datetime
from dateutil.parser import parse
import argparse
import extract_functions as extract
import prompts as prompt
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

def pdf_info(pdf_path, pdf_name):
        curr_path = pdf_path + pdf_name    
        ### Get Date and Title
        print('Getting date and title of the document...')
        document_title = extract.get_title(curr_path, model = 'gpt-3.5-turbo', pages=1)
        document_date = extract.get_date(curr_path, model = 'gpt-3.5-turbo', pages=1)
        try:
            parse(document_date)
            date_object = datetime.strptime(document_date, '%m/%d/%Y') 
            month = int(date_object.month)
            year = int(date_object.year)
            
        except ValueError:
            print(f"The provided date '{document_date}' is not valid.")
            month, year = "", ""
        
        
        print('Document Title: ' + document_title)
        print('')
        print(f'Document Date: {month}/{year}')
        print('------------')
        print('')

        ### Get commodities
        print('Detecting the primary and secondary commodities...')
        target_strings = ["commodit"]
        model = 'gpt-3.5-turbo-16k'
        comodities = extract.get_answ(pdf_path + pdf_name,target_strings,model, prompt.content, prompt.commodity_pr)
        for k,v in comodities.items():
            print(k + ': ', v)
        print('------------')
        print('')

        ### Get deposit types
        print('Detecting the deposit types...')
        #deposit_types_p = "./Deposit classification Scheme.xlsx"
        #deposit_groups = ', '.join(pd.read_excel(deposit_types_p, sheet_name='Deposit classification scheme',engine='openpyxl')['Deposit group'].unique())
        #deposit_types = ', '.join(pd.read_excel(deposit_types_p, sheet_name='Deposit classification scheme',engine='openpyxl')['Deposit type'].unique())

        target_strings = ["Deposit type"]
        res = extract.get_answ(pdf_path + pdf_name,target_strings,model, prompt.content, prompt.deposit_pr, replace_t=True)

        idx = 0
        document_deposit_types = {}
        document_deposit_types['deposit_type'] = []
        for dep in res['deposit types']:
            document_deposit_types['deposit_type'].append({"id": idx, "name": dep})
            idx +=1
        print(document_deposit_types)
        print('------------')
        print('')

        ### Get TOC
        print('Getting the Table of Content... hold tight, this might take some time...')
        TOC = extract.get_toc(curr_path)
        print(f"Here are the keys from TOC: \n {TOC.keys()}")
        print('Done. \n------------ \n')

        ### Extract location
        ### Location information in TOC
        print('Searching for location information within the available TOC...')
        loc_list = [x for x in TOC.keys() if "location" in x.lower() and "figure" not in x.lower()]
        print('Done. \n------------ \n')

        print('Searching for the pages where the location is mentioned: ')
        location_pages = extract.get_table_pages(curr_path,str(loc_list))
        print('Done. \n------------ \n')

        print('Getting relevant location information...')
        l = extract.get_location(curr_path,model='gpt-4',pages=list(location_pages.values()))
        print('Location info: ' + l)
        print('Done. \n------------ \n')

        ### Find relevant Table headers
        ### Tables in TOC
        print('Searching for relevant table headers within the available TOC...')
        ## add labels between list of tables and list of figures
        tables_list = [x for x in TOC.keys() if "table" in x.lower()]        
        print(f"Here is the list of tables: {tables_list}")
        model = 'gpt-4'
        pr = prompt.table_find + ", ".join(tables_list)

        response = extract.chat_completion_with_backoff(model=model, temperature=0, max_tokens=2000, stop='', messages=[
            {"role": "system", "content": prompt.table_content},
            {"role": "user", "content": pr},
            ])
        relevant_tables_toc = response['choices'][0]['message']['content']
        print('Done. \n------------ \n')
        
        print('Relevant tables:')
        try:
            for rel_tab in ast.literal_eval(relevant_tables_toc):
                print(rel_tab)
                
            print('Done. \n------------ \n')

            print('Searching for the pages where the relevant pages are mentioned: ')
            table_pages = extract.get_table_pages(curr_path,relevant_tables_toc)
            print(f"Here are the table_pages {table_pages}")
            print('Done. \n------------ \n')
            
        except(ValueError, SyntaxError) as e:
            print(f"ERROR: The relevant tables were not given in the correct format. Table pages will be empty \n")
            table_pages = {}
            
        
        
        
        pdf_dict = {
            "TOC": TOC,
            "document_title": document_title,
            "document_date_month": month,
            "document_date_year": year,
            "document_deposit_types": document_deposit_types,
            "relevant_tables": relevant_tables_toc,
            "table_pages" : table_pages,
            "location": l
        }
        
        with open(f"./stored_tables/{pdf_name[:-4]}_stored.json", 'w') as json_file:
            json.dump(pdf_dict, json_file, indent=2)
        
        
        

def run():
    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--pdf_p', type=str, help='Path to the reports folder', required=True)
    parser.add_argument('--pdf_name', type=str, help='The name of the document', required=True)
    parser.add_argument('--primary_commodity', type=str, help='Primary commodity we are interested in', required=True)
    parser.add_argument('--element_sign', type=str, help='The element sign of the primery commodity', required=True)
    parser.add_argument('--table_type', type=str, help='The type of information we need extracted from a table. Currently only "summary" and "zones" are accepted inputs', required=False)

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    pdf_p = args.pdf_p
    pdf_name = args.pdf_name
    primary_commodity = args.primary_commodity
    element_sign = args.element_sign
    table_type = args.table_type if args.table_type else 'summary'
    # EOF Arguments parsing
    curr_path = pdf_p + pdf_name
    
    if os.path.exists(f"./stored_tables/{pdf_name[:-4]}_stored.json"):
        print(f"Stored File {pdf_name[:-4]}_stored.json Exists: Opening saved File of variables \n")
    else:
        print(f"Stored File {pdf_name[:-4]}_stored.json DOES NOT Exist: Creating a the file \n")
        pdf_info(pdf_p,pdf_name)
        
    with open(f"./stored_tables/{pdf_name[:-4]}_stored.json", 'r') as json_file:
            # Load the JSON data into a Python dictionary
            pdf_data = json.load(json_file)

    ## get the saved values
    document_title = pdf_data["document_title"]  
    year = pdf_data["document_date_year"]
    month = pdf_data["document_date_month"]
    if month and year:
        date_string = month + "-" + year
        date_object = datetime.strptime(date_string, '%m-%Y')
        formatted_date = date_object.strftime('%m-%d-%Y')
    else:
       formatted_date = ""
    document_deposit_types = pdf_data["document_deposit_types"]
    table_pages = pdf_data["table_pages"]
    l = pdf_data['location'] 
    
    
    mineral_inventory = {}
    mineral_inventory['MineralInventory'] = []
    idx = 0
    uri = "https://w3id.org/usgs/z/4530692/MHU8MJUV"
    
    
    
    if len(table_pages) > 0:
        print('Getting relevant tables that contain: ' + table_type)
        relevant_tables = {}
        for title, page_num in table_pages.items():
            c = extract.get_relevant_tables(curr_path, page_num, primary_commodity, element_sign, table_type = table_type)
            if c == True:
                relevant_tables[title]=page_num
        print('Done.')
        print('Identified ' + str(len(relevant_tables)) + ' relevant tables:')
        for k,v in relevant_tables.items():
            print('Table ' + k + ' on page ' + str(v))
        print('------------')
        print('')

        print('Extracting information from the relevant pages...')
        overall_dict = []
        for title, page_num in relevant_tables.items():
            t = extract.extract_tables(curr_path, page_num, title, primary_commodity, element_sign)
            overall_dict.append(t)
        print('Done. \n------------ \n')
        
     
        for inner_dict in overall_dict:
            print("Inner Dict", inner_dict)
            for inner_sec in inner_dict:
                print("inner section",inner_sec)
                ore_dict = {}
                grade_dict = {}
                inner_dict = {}
                cutoff_grade_dict = {}
                
                page_num = inner_sec[5] 
                page_info_dict = {
                    'page':page_num
                }
                
                document_dict = {
                    'id':0,
                    'title':document_title,
                    'uri':uri,
                    'month':month,
                    'year':year
                }
            
                
                reference_dict = {
                    'id':idx,
                    'document':document_dict,
                    'page_info':page_info_dict
                }
                
                grade = inner_sec[4]
                grade_dict['grade_unit'] = 'percent'
                grade_dict['grade_value'] = extract.extract_floats(grade)[0]
                
                
                
                zone = inner_sec[0]
                category = inner_sec[1]
                cut_off = inner_sec[2]
                cutoff_grade_dict['grade_unit'] = 'percent'
                cutoff_grade_dict['grade_value'] = extract.extract_floats(cut_off)[0] 
                
                tonnage = str(inner_sec[3]).replace(',', '') 
                ore_dict['ore_unit'] = 'tonnes'
                ore_dict['ore_value'] = extract.extract_floats(tonnage)[0] 
                
                contained_metal = float(tonnage) * float(grade)/100

                inner_dict["id"] = idx
                inner_dict['commodity'] = primary_commodity
                inner_dict['category'] = category
                inner_dict['ore'] = ore_dict
                inner_dict['grade'] = grade_dict
                inner_dict['cutoff_grade'] = cutoff_grade_dict
                inner_dict['contained_metal'] = contained_metal
                inner_dict['reference'] = reference_dict
                inner_dict['date'] = formatted_date
                mineral_inventory['MineralInventory'].append(inner_dict)
                idx += 1
    else:
        print("Table Pages was Empty. Did not have information to fill out Mineral Inventory \n")

    MineralSite = {
        'id':0,
        'name':'',
        'location_info':l,
        'geology_info':'',
        'same_as':''
    }
    
    MineralSite.update(mineral_inventory)
    MineralSite.update(document_deposit_types)
    
    print("Writing JSON now \n-------------\n")
    print(json.dumps(MineralSite, indent=4,cls=extract.DateTimeEncoder)) 

    with open(f"extracted/{pdf_name[:-4]}_{table_type}_{str(int(time.time()))}.json", "w") as outfile:
        json.dump(MineralSite, outfile)   

if __name__ =="__main__":
    print("Running the Extraction \n-------------\n")
    run()