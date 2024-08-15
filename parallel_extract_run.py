"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import time
import os
import shutil
import pandas as pd
import sys
from extraction_package import ExtractionPipeline
import argparse
import ast


def run_from_metadata(comm_list, meta_file, folder_path, output_path, completed_path):
    meta_data = pd.read_csv(meta_file).fillna('')
    meta_data.head()

    
    all_files = os.listdir(completed_path)

    completed_records = []
    for filename in all_files:
        record_id, title = filename.split('_', 1)
        completed_records.append(record_id)

    print("Amount of files completed: ",len(completed_records))

    total = 0
    
    
    filenames = []
    commodity_list = []
    # need to add that it wasn't in the completed & then can run again

    for i, row in meta_data.iterrows():
        print(f"On file {i} of {meta_data.shape[0]}")
        comm_found = False
        identified = row['Identified Commodities'].split(",")
        filename = row['record_id'] + "_"+row['File Name']
        source_path = f'{folder_path}{filename}'
        
        for comm in identified:
            if comm.lower() in comm_list:
                total += 1
                comm_found = True
                
                if row['record_id'] in completed_records: 
                    pass
                else:
                    filenames.append(filename)
                    commodity_list.append(identified)
                    
        if not comm_found and os.path.exists(source_path):
            destination_path = f'{folder_path}not_found/{filename}'
            shutil.move(source_path, destination_path)
            print(f"Did not find commodity in {filename} \n")


        if len(filenames) == 5: 
            print("Starting Extractions")
            t = time.time()
            ExtractionPipeline.document_parallel_extract(
                folder_path,
                filenames,
                commodity_list,
                output_path
                    )

            
            print("\n-------------------------------------------------------------------------\n")
            print(f'parallel: {time.time()-t}')
            
            filenames, commodity_list = [], []
          
        
    print(f"found this many files with identified {total}")    
  
  
 
    
def run_folder_path(commodity_dictionary, folder_path, output_path, completed_path): 
    completed_files = os.listdir(completed_path)
    all_commodity_files = os.listdir(folder_path)

    completed_records, commodity_list = [], []
    for filename in completed_files:
        record_id, _ = filename.split('_', 1)
        completed_records.append(record_id)
        
    for filename in all_commodity_files:
        record_id, _ = filename.split('_', 1)
        if record_id in completed_records: 
            pass
        else:
            filenames.append(filename)
            commodity_list.append(commodity_dictionary[filename])


        if len(filenames) == 5: 
            print("Starting Extractions")
            t = time.time()
            ExtractionPipeline.document_parallel_extract(
                folder_path,
                filenames,
                commodity_list,
                output_path
                    )
            
            print("\n-------------------------------------------------------------------------\n")
            print(f'parallel: {time.time()-t}')
            
            filenames, commodity_list = [], []
            
    
def run(metadata):
    if metadata:
        run_from_metadata(comm_list=comm_list, meta_file=meta_file, 
        folder_path=folder_path, output_path=output_path, completed_path=completed_path)
    
        
    else:
        run_folder_path(commodity_dictionary, folder_path, output_path, completed_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--comm_list', type=str, help='List of commodities that you identify as related to the deposit type', required=True)
    parser.add_argument('--metafile', type=str, help='Path to generated metadata file', required=True)
    parser.add_argument('--folder_path', type=str, help='Path to stored reports', required=True)
    parser.add_argument('--output_path', type=str, help='Path to temporary storage of incomplete extractions', required=True)
    parser.add_argument('--completed_path', type=str, help='Path to storage of completed extractions', required=True)
    parser.add_argument('--commodity_dict', type=str, help='Dictionary of the list of commodities for each file.', required=True)
    
    # Parse the arguments
    args = parser.parse_args()
    
    comm_list = ast.literal_eval(args.comm_list)
    meta_file = args.metafile
    folder_path =  args.folder_path
    output_path = args.output_path
    completed_path = args.completed_path
    commodity_dictionary = args.commodity_dict
    
    ismetadata = True if len(meta_file) > 0 else False
  
    
    run(metadata=ismetadata,comm_list=comm_list, meta_file=meta_file, 
        folder_path=folder_path, output_path=output_path, completed_path=completed_path)
    
    
