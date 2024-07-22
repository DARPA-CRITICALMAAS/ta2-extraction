"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import os
import pandas as pd
import logging
import logging.config
from first_pass import HelperFunctions as helper

logging.config.fileConfig('config.ini')
logger = logging.getLogger("Downloader") 

def download_files(deposit_type, folder_name):
    df = pd.read_csv("./metadata/deposit_type_record_id.csv")
    df_deposit = df[df['deposit_type'] == deposit_type].reset_index()
    df_deposit_sorted = df_deposit.sort_values(by='confidence', ascending = False)
    m,n = df_deposit_sorted.shape
    logger.info(f"{m*0.1} or m: {m}")
    limit = m * 0.1

    if limit > 200:
        limit = 200
    elif m < 200:
        limit = m
    else:
        limit = m * 0.1
    logger.info(f"Limit: {limit}")
    
    download_dir = f"/Users/adrisheu/git_folders/ta2-extraction/reports/{folder_name}/"
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
    folder_name = "earth_metals"
    deposits = ["Carbonatite REE", "Peralkaline igneous HFSE- REE"]
    logger.info("Starting Download")
    for dep_type in deposits:
        download_files(dep_type, folder_name)