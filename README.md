# README for Extraction Package
This is the package that works to extract information from Mining Reports to gather deposit types, mineral inventory, mining report reference, and mining site information to create a larger Database. The most up to date package is stored in ./extraction_package. 

## Package Directory 
|-extraction_package/
    |---- __init__
    |---- extraction_pipeline : the main driver of the code
    |---- extraction_functions.py : stores all the functions needed to help the pipeline code
    |---- prompts: all prompts used
    |---- schema_formats: all the formats that match the schema derived by the larger TA2 team

## Installation (requires python >3.7 and pip)
1. Create virtual environment (python, anaconda, etc.)
2. In the project root: `pip install -r requirements.txt`

## How to run the single package for extraction
In the terminal: `python -m extraction_package.extraction_pipeline --pdf_p "/folder/path" --pdf_name  "filename.pdf" --primary_commodity "commodity" --element_sign "commodity_sign" --url "zoltero url"`

## How to run multiple files using the parallelization