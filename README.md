# README for Extraction Package
This is part of the TA2 project for USGS. This is the package that works to extract information from Mining Reports to gather deposit types, mineral inventory, mining report reference, and mining site information to create a larger Database. The most up to date package is stored in ./extraction_package. 

## Extraction Package Directory 
Note all loggers should be name similar to the file.
Launched July 31, 2024


extraction_package/ \
|    |---- \_\_init\_\_ \
|    |---- ExtractionPipeline : the main driver of the code \
|       |---- GeneralFunctions: all generalized functions that do not just relate to a single section \
|       |---- MineralInventory: code to generate the Mineral Inventory \
|       |---- MineralSite: Code to generate the Mineral Site and document reference information \
|       |---- Assistant Functions: all code that relates to call the LLM that is used
|       |---- DepositTypes : the code given to derive the deposit type candidates \
|       |---- ExtractPrompts: all prompts used \
|       |---- SchemaFormats: all the formats that match the schema derived by the larger TA2 team 

The extraction package holds all the major code for running the parallelized extraction of the mineral inventory. This code can be handled by calling a driver function such as parallel_extract_run.py. The driver function requires: the commodity you are working on, 
an acceptable list of commodities that we want to have found from the intial pass that indicates we want to extract that file, the filename of the metadata gathered and stored in a metadata folder, folderpath to the where the pdfs are stored to that given commodity.
 
## first pass Directory
The first pass directory stores all of the code that funs an initial first pass on a series of pdfs to gather the list of all commodities present in the file. This helps us determine whether or not we want to extract from that given file. It creates an output of a metadata file that gives a list of commodities within all files across a given commodity. 
extraction_package/ \
|    |---- \_\_init\_\_ \
|    |---- GatherCommodities: the main driver that goes through each file and extracts the commodities
|    |---- HelperFunctions: any generic prompts that were created just for this package
|    |---- prompts : all prompts used for the package

To run this directory you can call:  `python -m first_pass.GatherCommodities`

You need to update under the main function update the following variables:
* comm: the commodity of interest that you are looking at
* download_dir: filepath to the pdf files where the commodity pdfs are stored
* csv_output_path: the path where you want the metadata collected for that given commodity



## Installation (requires python >3.7 and pip)
1. Create virtual environment (python, anaconda, etc.)
2. In the project root: `pip install -r requirements.txt`


## How to run the single package for extraction
1. Add your openAI API key in the settings.py file under API_KEY variable
2. In the terminal at the root directory: `python -m extraction_package.extraction_pipeline --pdf_p "/folder/path" --pdf_name  "filename.pdf" --primary_commodity "commodity" --element_sign "commodity_sign" --url "zoltero url" --output_path "/folder/path"`




## How to run multiple files using the parallelization
1. Add your openAI API key in the settings.py file under API_KEY variable
2. Navigate to the parallel_run_extract.py
3. Update variables: 
    * commodity: the commodity you are working on 
    * comm_list: an acceptable list of commodities that we want to have found from the intial pass that indicates we want to extract that file
    * meta_file: the filename of the metadata gathered and stored in a metadata folder from running the first_pass
    *folderpath: folderpath to the where the pdfs are stored to that given commodity.
 


## Version Control
### current version 2.0
Major Changes
- LARGE overhaul to make code more scalable, readable, & all MPG's standards
- add logging, more try catch
- modularize the code into separate files

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


### OLD Extraction Package Directory 
extraction_package/ \
|    |---- \_\_init\_\_ \
| |---- extraction_pipeline : the main driver of the code \
|    |---- extraction_functions : stores all the functions needed to help the pipeline code \
|    |---- prompts: all prompts used \
|    |---- schema_formats: all the formats that match the schema derived by the larger TA2 team 
