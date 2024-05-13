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
1. Add your openAI API key in the settings.py file under API_KEY variable
2. In the terminal at the root directory: `python -m extraction_package.extraction_pipeline --pdf_p "/folder/path" --pdf_name  "filename.pdf" --primary_commodity "commodity" --element_sign "commodity_sign" --url "zoltero url" --output_path "/folder/path"`

## How to run multiple files using the parallelization
1. Add your openAI API key in the settings.py file under API_KEY variable
2. Navigate to the parallel_extraction.ipynb
3. Update variables: 
    - filenames: Names of the mining reports in your file path
    - url_list: DOI gathered from Zoltero
    - commodity: selected commodity of importance
    - commodity_sign: elemental sign of the commodity 
    - file_path: path to your Mining Reports that you want extracted
    - output_path: what folder you want extracted files to be stored
    Note: Many of these variables will not be needed in the future once we make a more autonomous package that integrates with the download of the reports


## Version Control
### current version 2.0
Major Changes
- LARGE overhaul to make code more scalable, readable, & all MPG's standards
- add logging, more try catch
- modularize the code into classes



### Past version explanations
1.2 Changes for 9 month, pushed to main DATE
reference : https://platform.openai.com/docs/assistants/tools/file-search
- Removed the need to look at total for categories or for zones
- Using gpt-4-Turbo
- updates to assistants v2 which includes JSON return
- add a separate check for just tonnage or units using chat GPT
- utilizing tenacity for any run status failures/errors
- Changing the author prompts
- Updating how we get pages by looking for key words

1.1 Change to the extraction clean-up
    - adding the instance check & removal of keys
    - new unit keys were added
    - this was used for cobalt
    - errors: not picking up all the rows, schema errors with removal of keys
1.0 Initial Prompts
    - this was done for copper & nickel & zinc