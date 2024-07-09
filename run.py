import time
import os
import shutil
import pandas as pd
import sys
from extraction_package import ExtractionPipeline


def finish_files(commodity):
    if commodity == "copper":
        comm_list = ['copper', 'rhenium', 'molybedenum', 'tellurium', 'gold']
        filename = 'phase_one_copper_top10percent'
        folder_path = "./reports/copper/"
    if commodity == "zinc":
        comm_list = ['zinc', 'lead', 'gallium', 'germanium', 'indium', 'silver', 'lead']
        filename = 'phase_one_mvt_zinc_top10percent'
        folder_path = "./reports/mvt_zinc/"
    
    if commodity == "nickel":
        comm_list = ['nickel', 'cobalt', 'copper', 'platinum', 'palladium', 'rhodium', 'ruthenium', 'iridium', 'osmium']
        filename = 'phase_one_nickel_copper_PGE_top10percent'
        folder_path = "./reports/nickel-copper-PGE/"
    
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
    
    
if __name__ == "__main__":
    commodity = "nickel"
    print(f"Working on commodity: {commodity}")
    finish_files(commodity=commodity)