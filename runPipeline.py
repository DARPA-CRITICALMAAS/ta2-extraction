import time
import os
import shutil
import pandas as pd
import sys
from extraction_package import pipeline as extract
from first_pass import HelperFunctions as helper
import json
import argparse
import ast
import statistics
import pickle
import re


def extract_commodity(text):
    if not isinstance(text, str):  # Ensure text is a string
        return []
    return re.findall(r'Commodity:([^;]+)', text)


def save_unfinished_files(folder_path):
    ## Get the list where name has NI_43 in them
    ## save that to then rerun
    directory_path = "/Users/adrisheu/git_folders/ta2-minmod-data/data/mineral-sites/inferlink/mining-report/"
    save_file, zotero_files, completed_files = [], [], []
    # Iterate through all files in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        # Check if the file is a JSON file
        if filename.endswith(".json"):
            try:
                with open(file_path, "r") as json_file:
                    # Load the file as JSON
                    data = json.load(json_file)
                    print(f"Successfully loaded JSON from {filename}")



                    if "NI 43-101" in data[0]['name']:
                        if filename[0] == "0":
                            save_file.append(filename.split(".")[0])
                            # print("saved_file\n")
                        else:
                            zotero_id = data[0]['record_id']
                            zotero_files.append(zotero_id)
                            # print(f"Here is zotero ID: {zotero_id} \n\n")
                    else:
                        # print("Completed \n\n")
                        completed_files.append(filename)
    
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                
    ## next step          
    with open('./metadata/zotero_cdr_id.pickle', 'rb') as file:
        data = pickle.load(file)
        
    
    for zotero_id in zotero_files:
        zotero_id = zotero_id.split("/")[1]
        # print(zotero_id)
        if zotero_id in data: 
            cdr_id = data[zotero_id]['id']
            save_file.append(cdr_id)
    
    for file in save_file:
        if file in completed_files:
            pass
        else:
            helper.download_document(file, folder_path)
            
    

     
      

if __name__ == '__main__':
    with open('./metadata/zotero_cdr_id.pickle', 'rb') as file:
        cdr_data = pickle.load(file)
        
    zotero_df = pd.read_csv('./metadata/Zotero_files.csv')
        
    folder_path = "./reports/unfinished/"
    
    # desired_commodity = "graphite"
    
    # save_unfinished_files(folder_path)
    # print("finished downloading files\n")
    
    output_folder_path = "./extracted/updated_files/"
    
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]

    completed_files = []
    if os.path.exists(output_folder_path):
        completed_files = [
            f[:-5]
            for f in os.listdir(output_folder_path) if f.endswith(".json")
        ]
        
    print(f"Amount completed: {len(completed_files)}")
    print(f"completed: {completed_files}")

    filenames = []
    for idx, file in enumerate(pdf_files):
        print(f"Looking at file: {file}\n")
        print(f"On file {idx+1} out of {len(pdf_files)}")
        record_id = file.split("_")[0]
        
        if record_id not in completed_files:
            filenames.append(file)
            if len(filenames) == 5: 
                print("Starting Extractions")
                t = time.time()
                extract.document_parallel_extract(folder_path, filenames, output_folder_path)
                print("Finished set of files in :", time.time() - t)
                filenames = []
        else:
            print("already completed file\n")
            
    # must do a final pass to get the last set in case theres an outlier
    extract.document_parallel_extract(folder_path, filenames, output_folder_path)