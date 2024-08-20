# README for Extraction Package
This code is a part of the TA2 project for USGS. This is the package that works to extract information from Mining Reports to gather deposit types, mineral inventory, mining report reference, and mining site information to create a larger Database. The most up to date package is stored in ./extraction_package. 


## Recommendation for Running this package
To exploit all the advantages of this package, you want to use it for the entire process of downloading the files to extracting all the commodities within them. This walkthrough starts from a specific commodity/deposit type pair. 
### Steps
0. Make sure all variables in the settings.py are correctly formatted (ie API keys)
1. Run the download_files.py to get all files connected to the commodity/deposit type pair: 

    1a. run: `python -u download_files.py --download_dir 'path you want to download too' --deposits '[list of deposit types]' --report_limit 'Max amount of reports you want to download. If no limit leave empty' `
    
    **Note** A valid deposits list is ["mvt zinc-lead"].

2. Run the first pass package to gather a list of all commodities within a given file.

    2a. run `python -um first_pass.GatherCommodities --download_dir 'path to stored reports' --csv_output 'Full Path to where and what you want to name the csv metadata file' `

3. Run the extraction package to get the extractions
    
    3a. run `python -u parallel_extract_run.py --comm_list '[List of commodities as strings that you identify as related to the deposit type]' --metafile 'Path to generated metadata file' --folder_path 'Path to stored reports' --output_path 'Path to temporary storage of incomplete extractions' --completed_path 'Path to storage of completed extractions' --commodity_dict 'Dictionary of the list of commodities for each file' `

    **Note** if there is no metadata file you can leave it as an empty string. If there is a metadata file then commodity dictionary can be left as an empty string. Also a valid format for the comm_list is ["zinc", "lead"]. Also a valid format for the comm_list is ["zinc", "lead"]. For commodity_dict is {"filename": ["zinc"]}.

For further explaination or information of each of these steps refer to the sections below. 


## Extraction Package Directory 
Note all loggers should be name similar to the file.
Launched Aug 14, 2024


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

The extraction package holds all the major code for running the parallelized extraction of the mineral inventory. This code can be handled by calling a driver function such as parallel_extract_run.py. 

### Description of Variables
* **comm_list**: an acceptable list of commodities that we want to have found from the intial pass that indicates we want to extract that file
* **meta_file**: the filename of the metadata gathered and stored in a metadata folder from running the first_pass
* **folderpath**: folderpath to the where the pdfs are stored to that given commodity.
* **output_path**: output folder path where you want extractions to be temporarily stored before they are completed
* **completed_path**: output folder path where you want fully completed extractions (ie all three sections) stored in
* **commodity_dictionary**: this should be a dictionary where the filename is a key and the value is a list of found commodities in the file. 

### How to run
**Note**: In order to correctly run this section you must have previously run the first pass to generate the metadata file that will be used for the extractions. Please refer to section first pass directory to generate that file.
**Note**: the function expects that the files are downloaded with the file name as CDR_DOCUMENT_ID underscore then file title. For example: 02003096a4646d77019ce2e76ba93c8e2242a7a8ae7734176781080368f32772c9_NI 43-101 Technical Report for the Rovina Valley project in Romania dated March, 2022. If you want to download files following this format please refer to the download_files.py

0. Make sure all variables in the settings.py are correctly formatted (ie API keys)
1. run `python -u parallel_extract_run.py --comm_list '[List of commodities as strings that you identify as related to the deposit type]' --metafile 'Path to generated metadata file' --folder_path 'Path to stored reports' --output_path 'Path to temporary storage of incomplete extractions' --completed_path 'Path to storage of completed extractions' --commodity_dict 'Dictionary of the list of commodities for each file' `

**Note** if there is no metadata file you can leave it as an empty string. If there is a metadata file then commodity dictionary can be left as an empty string. Also a valid format for the comm_list is ["zinc", "lead"]. For commodity_dict is {"filename": ["zinc"]}.
 
## First pass Directory
The first pass directory stores all of the code that creates an initial first pass on pdfs to generate a list of all commodities present in a given file. This helps us determine whether or not we want to extract from that given file. It creates an output of a metadata file that gives a list of commodities within all files across a given commodity. 
extraction_package/ \
|    |---- \_\_init\_\_ \
|    |---- GatherCommodities: the main driver that goes through each file and extracts the commodities \
|    |---- HelperFunctions: any generic prompts that were created just for this package \
|    |---- prompts : all prompts used for the package \

### How to run
0. Make sure all variables in the settings.py are correctly formatted (ie API keys) 
1. To run this directory you can call:  `python -um first_pass.GatherCommodities --download_dir 'path to stored reports' --csv_output 'Path to where you want to download reports'`

## Download Files
The python file download_files.py works by using the SRI generated predictions of deposit types, which is sotred in the metadata directory. This works by downloading a limited amount of files from a given commodity type by creating an API request to the CDR.

### How to run
0. Make sure all variables in the settings.py are correctly formatted (ie API keys) 
1. To run: `python -u download_files.py --download_dir 'path you want to download too' --deposits '[list of deposit types]' --report_limit 'Max amount of reports you want to download. If no limit leave empty' `

**Note** A valid deposits list is ["mvt zinc-lead"].

## Installation (requires python >3.7 and pip)
1. Create virtual environment (python, anaconda, etc.)
2. In the project root: `pip install -r requirements.txt`


## How to run the single package for extraction
1. Add your openAI API key in the settings.py file under API_KEY variable
2. In the terminal at the root directory: `python -m extraction_package.extraction_pipeline --pdf_p '/folder/path' --pdf_name  'filename.pdf' --commodity_list '[List of commodities expected in the file]' --output_path '/folder/path' `

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
