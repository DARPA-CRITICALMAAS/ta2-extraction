import time
import os
import shutil
import pandas as pd
import sys
from extraction_package import extractionPipeline as extract
import argparse
import ast
import statistics



if __name__ == '__main__':
    print("In testRun.py")
    folder_path = "./reports/copper/"


    output_folder_path = "./extracted/look_at/copper/"
    reference_path = "./automatic_evaluation/data/gt_csv_format/"
    
    report_ids = [
        entry.name
        for entry in os.scandir(reference_path)
        if entry.is_dir()
    ]

    pdf_files = [
        file for file in os.listdir(folder_path)
        if file.endswith('.pdf') and file.split('_')[0] in report_ids
    ]
    


    filenames = []
    for file in pdf_files:
        filenames.append(file)
        if len(filenames) == 5: 
            print("Starting Extractions")
            t = time.time()
            extract.document_parallel_extract(folder_path, filenames, output_folder_path)
            print("Finished set of files in :", time.time() - t)
            filenames = []
            
    # must do a final pass to get the last set in case theres an outlier
    extract.document_parallel_extract(folder_path, filenames, output_folder_path)