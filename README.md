# README for Extraction Package
This is part of the TA2 project for USGS. This is the package that works to extract information from Mining Reports to gather deposit types, mineral inventory, mining report reference, and mining site information to create a larger Database. The most up to date package is stored in ./extraction_package. 

## Extraction Package Directory 
extraction_package/ \
|    |---- \_\_init\_\_ \
| |---- extraction_pipeline : the main driver of the code \
|    |---- extraction_functions : stores all the functions needed to help the pipeline code \
|    |---- prompts: all prompts used \
|    |---- schema_formats: all the formats that match the schema derived by the larger TA2 team 

## Installation (requires python >3.7 and pip)
1. Create virtual environment (python, anaconda, etc.)
2. In the project root: `pip install -r requirements.txt`

## How to run the single package for extraction
In the terminal at the root directory: `python -m extraction_package.extraction_pipeline --pdf_p "/folder/path" --pdf_name  "filename.pdf" --primary_commodity "commodity" --element_sign "commodity_sign" --url "zoltero url"`

## How to run multiple files using the parallelization
1. Navigate to the parallel_extraction.ipynb
2. Update variables: 
    - filenames: Names of the mining reports in your file path
    - url_list: DOI gathered from Zoltero
    - commodity: selected commodity of importance
    - commodity_sign: elemental sign of the commodity 
    - file_path: path to your Mining Reports that you want extracted
    - output_path: where you want extracted files to be stored
    Note: Many of these variables will not be needed in the future once we make a more autonomous package that integrates with the download of the reports