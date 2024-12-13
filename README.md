# README for Extraction Package
This code is a part of the TA2 project for USGS. This is the package that works to extract information from Mining Reports to gather deposit types, mineral inventory, mining report reference, and mining site information to create a larger Database. The most up to date package is stored in ./extraction_package. 


## Recommendation for Running this package
To exploit all the advantages of this package, you want to use it for the entire process of downloading the files to extracting all the commodities within them. This walkthrough starts from a specific commodity/deposit type pair. 

### How to run Docker Image
1. Clone the Repository: `git clone git@github.com:DARPA-CRITICALMAAS/ta2-extraction.git `
2. Build the Docker Image: `docker build -t -my-extraction-app .`
3. Running the Docker Container: 
``` 
    docker run \
    -v /path/to/stored/reports/ta2-extraction/reports:/app/reports \
    -v /path/to/stored/reports/ta2-extraction/output:/app/output \
    my-extraction-app \
    python -m extraction_package.pipeline \
    --pdf_p "/app/reports/" \
    --pdf_name "FileName.pdf" \
    --output_path "/app/output/"
```

**Note**: Make sure the the directories are for saving the output and finding the reports are correctly named. This will only run one file at a time. --pdf_p: the pathway to where reports are stored. --pdf_name: is the name of the file that you want to extract from. --output_path: folder directory where you want to store the output.

## Extraction Package Directory 
Note all loggers should be name similar to the file.
Launched Aug 14, 2024


extraction_package/ \
|    |---- \_\_init\_\_ \
|    |---- ExtractionPipeline : the main driver of the code \
|       |---- genericFunctions: all generalized functions that do not just relate to a single section \
|       |---- mineralInventoryHelp: code to generate the Mineral Inventory \
|       |---- documentRefHelp: Code to generate the Mineral Site and document reference information \
|       |---- LLMFunctions: all code that relates to call the LLM that is used \
|       |---- LLMModels: all formats for structured outputs \
|       |---- depositTypesHelp : the code given to derive the deposit type candidates \
|       |---- extractionPrompts: all prompts used \
|       |---- schemaFormats: all the formats that match the schema derived by the larger TA2 team 

The extraction package holds all the major code for running the parallelized extraction of the mineral inventory. This code can be handled by calling a driver function such as runPipeline.py.

### Description of Variables
* **file_name**: the filename of the pdf that you want to extract from
* **folderpath**: folderpath to the where the pdfs are stored to that given commodity.
* **output_path**: output folder path where you want fully completed extractions (ie all three sections) stored in


### How to run One File
0. Make sure all variables in the settings.py are correctly formatted (ie API keys)
1. Create virtual environment
2. Install required dependencies: `pip install -r requirements.txt`
3. Run Pipeline for one File which must already be downloaded locally: `python -m extraction_package.pipeline --pdf_p "/path/to/reports/" --pdf_name "FileName.pdf" --output_path "/path/to/stored/output/"`


## Download Files
The python file download_files.py works by using the SRI generated predictions of deposit types, which is sotred in the metadata directory. This works by downloading a limited amount of files from a given commodity type by creating an API request to the CDR.

### How to run
0. Make sure all variables in the settings.py are correctly formatted (ie API keys) 
1. To run: `python -u download_files.py --download_dir 'path you want to download too' --deposits '[list of deposit types]' --report_limit 'Max amount of reports you want to download. If no limit leave empty' --doc_ids '[List of document ids that are in the CDR]' `

**Note** A valid deposits list is ["mvt zinc-lead"]. If you want to download via doc_ids leave deposits empty. If you want to download using deposits only without any specific doc_ids leave doc_ids as an empty list. 

## First pass Directory : Might not be needed Anymore
The first pass directory stores all of the code that creates an initial first pass on pdfs to generate a list of all commodities present in a given file. This helps us determine whether or not we want to extract from that given file. It creates an output of a metadata file that gives a list of commodities within all files across a given commodity. 
extraction_package/ \
|    |---- \_\_init\_\_ \
|    |---- GatherCommodities: the main driver that goes through each file and extracts the commodities \
|    |---- HelperFunctions: any generic prompts that were created just for this package \
|    |---- prompts : all prompts used for the package \

### How to run
0. Make sure all variables in the settings.py are correctly formatted (ie API keys) 
1. To run this directory you can call:  `python -um first_pass.GatherCommodities --download_dir 'path to stored reports' --csv_output 'Path to where you want to download reports'`

## Installation (requires python >3.7 and pip)
1. Create virtual environment (python, anaconda, etc.)
2. In the project root: `pip install -r requirements.txt`


## How to run the single package for extraction
1. Add your openAI API key in the settings.py file under API_KEY variable
2. In the terminal at the root directory: `python -m extraction_package.extraction_pipeline --pdf_p '/folder/path' --pdf_name  'filename.pdf' --output_path '/folder/path' `

## Version Control
### Current Version 3.0
Major Changes
- Removal of assistants to use a more generic model for longevity
- change approach of how to get page number
- utilization of structured outputs and openAI improvements for models 4o
- Working on adding a filtered extraction 

### Previous Version 2.0: extraction_package
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


### OLD Extraction Package Directory v1
extraction_package/ \
|    |---- \_\_init\_\_ \
| |---- extraction_pipeline : the main driver of the code \
|    |---- extraction_functions : stores all the functions needed to help the pipeline code \
|    |---- prompts: all prompts used \
|    |---- schema_formats: all the formats that match the schema derived by the larger TA2 team 
