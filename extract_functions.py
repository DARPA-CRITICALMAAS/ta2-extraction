import PyPDF2
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential
)  # for exponential backoff
import openai
import time
import json
import warnings
import re
import ast
from datetime import datetime
import prompts as prompts
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')


openai.api_key = "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"



@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(16))
def chat_completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

# Functions
def search_text_in_pdf(pdf_path, target_string):
    page_numbers = []
    
    # Open the PDF file in binary mode
    with open(pdf_path, 'rb') as file:
        
        # Create a PDF reader
        pdf = PyPDF2.PdfReader(file)
        
        # Iterate over each page
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_new = ' '.join(text.replace("\t", " ").split()).lower()
            # Check if target string is in the page's text
            if target_string.lower() in text_new:
                page_numbers.append(page_num)            
    return page_numbers

def get_answ(pdf_path,target_strings,model, content, pr, replace_t = False):
    all_matching_pages = []
    for target_string in target_strings:
        matching_pages = search_text_in_pdf(pdf_path, target_string)
        all_matching_pages += matching_pages
    if len(all_matching_pages)==0:
        return({})

    res = {}
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        all_text = ''
        for matching_page in matching_pages:
            
            page = pdf.pages[matching_page]
            text = page.extract_text()
            all_text = all_text + '/n' + text
        if replace_t:
            all_text = all_text.replace("\t", " ")
            
        response = chat_completion_with_backoff(model=model, temperature=0, max_tokens=4000, stop='.', messages=[
        {"role": "system", "content": content},
        {"role": "user", "content": pr+all_text},
        ])
        res = json.loads(response['choices'][0]['message']['content'])
        time.sleep(0.1)
    print(f"Relevant pages that possibly contain the information: {matching_pages}")
    return(res)

def get_title(pdf_path,model='gpt-3.5-turbo',pages=2):
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        all_text = ''
        for page_num in range(pages):
            page = pdf.pages[page_num]
            text = page.extract_text()
            all_text = all_text + text
        response = chat_completion_with_backoff(model=model, temperature=0, max_tokens=2000, stop='', messages=[
            {"role": "system", "content": prompts.content},
            {"role": "user", "content": prompts.get_title_pr + all_text + 'The title is:'},
            ])
            #print(table_pr.replace("__TABLE_TITLE__",title) + text)
        res = response['choices'][0]['message']['content']
    return(res)

def get_date(pdf_path,model='gpt-3.5-turbo',pages=2):
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        all_text = ''
        for page_num in range(pages):
            page = pdf.pages[page_num]
            text = page.extract_text()
            all_text = all_text + text
        response = chat_completion_with_backoff(model=model, temperature=0, max_tokens=2000, stop='', messages=[
            {"role": "system", "content": prompts.content},
            {"role": "user", "content": prompts.get_date_pr + all_text + 'The date is:'},
            ])
            #print(table_pr.replace("__TABLE_TITLE__",title) + text)
        res = response['choices'][0]['message']['content']
    return(res)

def is_json_compatible(string):
    try:
        json.loads(string)
        return True
    except ValueError:
        return False

def get_toc(file_path):
    with open(file_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)

        all_res = {}
        i=0
        y=False
        n=0
        while n<2:
            page = pdf.pages[i]
            text = page.extract_text()
            model_yes_no = 'gpt-4'
            response_yes_no = chat_completion_with_backoff(model=model_yes_no, temperature=0, max_tokens=2000, stop='.', messages=[
                {"role": "system", "content": prompts.content_toc},
                {"role": "user", "content": prompts.content_yes_no + text},
                ])
            res_yes_no = response_yes_no['choices'][0]['message']['content']
            time.sleep(2)
            if 'yes' in res_yes_no.lower():
                print(f"Is there a TOC on page {i}: {res_yes_no} ...Extracting TOC...")
                y=True
                model = 'gpt-3.5-turbo'
                response = chat_completion_with_backoff(model=model, temperature=0, max_tokens=2000, stop='', messages=[
                    {"role": "system", "content": prompts.content_toc},
                    {"role": "user", "content": prompts.content_pr + text},
                    ])
                res = response['choices'][0]['message']['content']
                
                if is_json_compatible(res):
                    ans = json.loads(res)
                    for key in ans.keys():
                        all_res[key] = ans[key]
            else:
                if y == True: n+=1
                print(f"Is there a TOC on page {i}: {res_yes_no}")
                    
            i+=1

    return all_res

def get_table_pages(pdf_path,relevant_tables):
    rel_tables = ast.literal_eval(relevant_tables)
    tables_pages = {}
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            text = text.replace(" ", "").lower()
            for st in rel_tables:
                if st.lower().replace(" ","") in text:
                    tables_pages[st] = page_num
    return(tables_pages)

def extract_tables(pdf_path, page_num, title, primary_commodity, element_sign):
    uniq_dict = {}
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        page = pdf.pages[page_num]
        text = page.extract_text()
        model = 'gpt-4'
        response = chat_completion_with_backoff(model=model, temperature=0, max_tokens=2000, stop='', messages=[
            {"role": "system", "content": prompts.content},
            {"role": "user", "content": prompts.table_pr.replace("__TABLE_TITLE__",title).replace("__PRIMARY_COMMODITY__", primary_commodity).replace("__ELEMENT_SIGN__", element_sign) + text},
            ])
        #print(table_pr.replace("__TABLE_TITLE__",title) + text)
        res = response['choices'][0]['message']['content']
        #print(res)
        match = re.search(r'\{.*\}', res, re.DOTALL)
        if match:
            extracted_content = match.group(0).replace("'", '"')
            # print(extracted_content)
            if is_json_compatible(extracted_content):
                ans = json.loads(extracted_content)
                for inner_dict in ans.values():
                    inner_dict['page_num']= page_num + 1
                    if tuple(inner_dict.values()) in uniq_dict.keys():
                        pass
                    else:
                        uniq_dict[tuple(inner_dict.values())] = "seen"
                    
            # else:
            #     print("No match found.") 
    return uniq_dict

def get_relevant_tables(pdf_path, page_num, primary_commodity, element_sign, table_type = "summary"):
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        page = pdf.pages[page_num]
        text = page.extract_text()
        model = 'gpt-4'
        if table_type == "summary":
            pr = prompts.table_summary.replace("__PRIMARY_COMMODITY__", primary_commodity).replace("__ELEMENT_SIGN__", element_sign) + text
        if table_type == "zones":
            pr = prompts.table_zones.replace("__PRIMARY_COMMODITY__", primary_commodity).replace("__ELEMENT_SIGN__", element_sign) + text
        response = openai.ChatCompletion.create(model=model, temperature=0, max_tokens=2000, stop='', messages=[
            {"role": "system", "content": prompts.content},
            {"role": "user", "content": pr},
            ])
        res = response['choices'][0]['message']['content']
        if res == "Yes": 
            return (True)
        if res == "No": 
            return (False)
    return (False)

def get_location(pdf_path,model='gpt-3.5-turbo',pages=[1,2]):
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        all_text = ''
        for page_num in pages:
            page = pdf.pages[page_num]
            text = page.extract_text()
            all_text = all_text + text
        response = chat_completion_with_backoff(model=model, temperature=0, max_tokens=2000, stop='', messages=[
            {"role": "system", "content": prompts.content},
            {"role": "user", "content": prompts.get_location_pr + all_text + 'The location is:'},
            ])
            #print(table_pr.replace("__TABLE_TITLE__",title) + text)
        res = response['choices'][0]['message']['content']
    return(res)


class DateTimeEncoder(json.JSONEncoder):
    ''' Custom encoder for datetime objects '''
    def default(self, obj):
        if isinstance(obj, datetime):
            # Format the date however you like here
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
    
def extract_floats(s):
    pattern = r'[-+]?\d*\.\d+|\d+'
    # Find all matches of the pattern in the string
    matches = re.findall(pattern, s)
    if not matches:
        return ['']
    return [float(match) for match in matches]

# EOF functions