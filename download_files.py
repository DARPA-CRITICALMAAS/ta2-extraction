"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import os
import pandas as pd
import logging
import logging.config
import argparse
import ast
from first_pass import HelperFunctions as helper

logging.config.fileConfig('config.ini')
logger = logging.getLogger("Downloader") 

def ensure_trailing_slash(path):
    normalized_path = os.path.normpath(path)
    
    if os.path.isdir(normalized_path) and not normalized_path.endswith(os.sep):
        normalized_path += os.sep
    
    return normalized_path

def download_files(deposit_type, download_dir, report_limit):
    df = pd.read_csv("./metadata/deposit_type_record_id.csv")
    df_deposit = df[df['deposit_type'] == deposit_type].reset_index()
    df_deposit_sorted = df_deposit.sort_values(by='confidence', ascending = False)
    m,n = df_deposit_sorted.shape
    logger.info(f"{m*0.1} or m: {m}")
    
    report_limit = m if not report_limit else int(report_limit)
    limit = m * 0.1

    if limit > report_limit:
        limit = report_limit
    elif m < report_limit:
        limit = m
    else:
        limit = m * 0.1
    logger.info(f"Limit: {limit}")
    
    
    count = 1
    for index, row in df_deposit_sorted.iterrows():
        logger.info(f"On file number: {count} out of {limit}")
        if count < limit:
            doc_id = row['record_id']
            helper.download_document(doc_id, download_dir)
            logger.info(f"Document {doc_id} downloaded successfully")
        else:
            break
            
        count += 1
        
        

    
    
        
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Named arguments.")

    # Define named arguments
    parser.add_argument('--deposits', type=str, help='list of deposit types you want to download', required=True)
    parser.add_argument('--download_dir', type=str, help='Path to where you want to download reports', required=True)
    parser.add_argument('--report_limit', type=str, help='Max amount of reports you want to download. If no limit leave empty', required=True)
    parser.add_argument('--doc_ids',type=str, help='Download exact doc_id', required=True)
   
   
    # Parse the arguments
    args = parser.parse_args()
    deposits = ast.literal_eval(args.deposits)
    doc_id_list = ast.literal_eval(args.doc_ids)
    download_dir = ensure_trailing_slash(args.download_dir)
    report_lim = args.report_limit
    logger.info("Starting Download")
    
    for dep_type in deposits:
        download_files(dep_type, download_dir, report_lim)
        
    for doc_id in doc_id_list:
        helper.download_document(doc_id, download_dir)