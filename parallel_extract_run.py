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


def finish_files(commodity, comm_list, filename, folder_path):

    
    meta_data = pd.read_csv(f'./metadata/{filename}.csv').fillna('')
    meta_data.head()

    completed_path = f"./extracted/twelve_month/{commodity}/completed/"
    all_files = os.listdir(completed_path)

    completed_records = []
    for filename in all_files:
        record_id, title = filename.split('_', 1)
        completed_records.append(record_id)

    print("Amount of files completed: ",len(completed_records))

    total = 0
    
    output_path = f"./extracted/twelve_month/{commodity}/"
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
            print(f"Did not find commodity in {filename} ")


        if len(filenames) == 5: 
            print("Starting Extractions")
            t = time.time()
            ExtractionPipeline.document_parallel_extract(
                folder_path,
                filenames,
                commodity_list,
                output_path
                    )
            
            # # Single run
            # for i, filename in enumerate(filenames):
            #     t = time.time()
            #     ExtractionPipeline.run(folder_path, filename, commodity_list[i], output_path)
            #     print(f'Run for file {filename}: {time.time()-t}')
            
            
            
            print("\n-------------------------------------------------------------------------\n")
            print(f'parallel: {time.time()-t}')
            # sys.exit()
            filenames, commodity_list = [], []
          
        
    print(f"found this many files with identified {total}")    
    
    
if __name__ == "__main__":
    commodity = "earth_metals"
    print(f"Working on commodity: {commodity}")
    
    comm_list = ["yttrium", "scandium", "niobium", "lanthanum", "cerium", "praseodymium", 
                "neodymium", "samarium", "europium", "gadolinium", "terbium", 
                "dysprosium", "holmium", "erbium", "thulium", "ytterbium", "lutetium", "rare earth elements"]
    
    filename = f'phase_one_{commodity}_top10percent'
    folder_path = f"./reports/{commodity}/"
    finish_files(commodity=commodity, comm_list=comm_list, filename=filename, folder_path=folder_path)