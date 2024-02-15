import pandas as pd

# Prompt templates
content = """You are a mining assistant, knowledgable in geology and skilled in understanding mining reports. You can extract information about mines, ore and minerals."""

commodity_pr = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a text from a mining report and you have to find out what are the primary commodities and secondary commodities. 
The output should be in the following format: 
{"primary commodities": [primary commodity 1, primary commodity 2], "secondary commodities": [secondary commodity 1, secondary commodity 2]

Note that there could be no primary and secondary commodities mentioned, and in that case you should return None where appropriate.
Here is the text: 
"""
## Deposits
deposit_types_p = "./Deposit classification Scheme.xlsx"
deposit_types = ', '.join(pd.read_excel(deposit_types_p, sheet_name='Deposit classification scheme',engine='openpyxl')['Deposit type'].unique())

deposit_pr = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a text from a mining report and you have to find out what are the deposit types in this mine. You can chose only from 
the provided list of the deposit types. You can chose one or more deposit types. If it is unknown, answer None.
The output should be in the following format: {"deposit types": [deposit type 1, deposit type 2]}

Note that there could be no deposit types mentioned, and in that case you should return None where appropriate.
Here is the list of the provided deposit types: """ + deposit_types + ", None." + """ Here is the text from the report: 
"""
#### TOC
content_toc = "You are a mining assistant, knowledgable in geology and skilled in understanding mining reports. You can extract information about tables of contents from reports."
content_pr = """You are a documentation expert and you can understand very well the table of contents of the mining reports.
You will be provided a table of contents and you need to understand it and return the number and page for each section and all subsections in a given table of content. Please include
all sections within the list of tables and list of figures. If the subsections under the list of tables do not have the label table please append 'table' to the beggining of that section's name.
The output should be in the following format: 
{"text":["number", "page"],  "text":["number", "page"]}

For example: 
{"Information Sources and References":["2.5", "7"],
"Reliance on Experts":["3.0", "7"]}

If there are no pages visible or you think there is no table of content in a text, return None.
Here is the text: 
"""
content_yes_no = """You are a documentation expert and you can understand very well the table of contents of the mining reports.
You will be provided a text and you need to decide if the text represents a table of contents. 
If a given text represents a table of contents, answer Yes. Otherwise answer No. 
You can only answer with Yes or No.
Here is the text: 
"""
### get header
content_header = """You are a mining assistant, knowledgable in geology and 
skilled in understanding mining reports. You can extract the header of the section from the
given text."""
content_find = """You are a documentation expert and you can understand very well the 
contents of the mining reports. You will be provided a section of a paper and 
you need to understand it and see if in the text the term given is used as a header 
on the given page.
The output should only given as "Yes" or "No". Here is the  
"""
## returning from the tables
response_example = """{'Line1': {'Zone': 'zone', 'Classification': 'classification', 'element Cut-Off': 'cut-off', 'element Tonnage': 
'tonnage', 'element Grade %': 'element % number' }, 'Line2': {'Zone': 'zone', 'Classification': 'classification', 'element Cut-Off': 
'cut-off', 'element Tonnage': 'tonnage', 'element Grade %': 'element % number'},...}"""

table_pr = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a text from a mining report and a table name. You have to find out what are the different combinations of Zones (which is the name of a location),
classification (which is either indicated, measured or inferred), cut-off (represented as a decimal), tonnage (in Tonnes) and 
grade (given in %) from the given table in the text. Please extract the name of the element and place it in the output
below without any additional text. We only care about the table with title: __TABLE_TITLE__
Note we only care about the mineral __PRIMARY_COMMODITY__ represented by __ELEMENT_SIGN__.

For each line in the table create a nested dictionary that follows this json file format as the response:  
""" + response_example

# find tables that mention mineral resources from TOC
table_content = """You are a mining assistant, knowledgable in geology and skilled in understanding mining reports. You can understand tables in mining reports"""
table_find = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a list of tables in a document. You should extract the FULL names of the tables if their
name refers to any of the following: "mineral resource estimate", "resource estimate", "cut-off sensitivity", "measured, indicated or inferred resources".
Remember to extract only titles of the tables in list format. For example: ["Title of table1", "Title of table2"].
If you cannot find any table that fits the criteria, return None.
Here is the list of tables: """

#find specific tables from already selected table pages from TOC
table_summary = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a text that contains a table. We are interested in tables that show mineral resource estimate for __PRIMARY_COMMODITY__ represented by __ELEMENT_SIGN__.
We are only interested in tables that show summary of results: no zones should be mentioned and no various cut-off values should be mentioned in a table.
If a page contains a table that shows summary resource estimates with a single cut-off value and not mentioning any zones, answer Yes. Otherwise answer No. 
You can only answer Yes or No.
Here is the text: 
"""

table_zones = """You are a geology expert and you are very good in understanding mining reports. You will be given 
a text that contains a table. We are interested in tables that show mineral resource estimate for __PRIMARY_COMMODITY__ represented by __ELEMENT_SIGN__.
We are only interested in tables that show results with zones. Zones should be mentioned and also various cut-offs should be mentioned in a table.
If a page contains a table that shows resource estimates with multiple cut-off values and multiple zones, answer Yes. Otherwise answer No. 
You can only answer Yes or No.
Here is the text: 
"""

#Get title
get_title_pr = """You are a geology expert and you are very good in understanding mining reports. You will be given a mining report and you need to extract a main title of the document.
Return a complete main title of a document. Return only a complete title, no extra words. 
Here is a text:
"""

#Get date
get_date_pr = """You are a geology expert and you are very good in understanding mining reports. You will be given a mining report and you need to extract a report date.
Return only a report date in the following form: "mm/dd/yyyy". For example: "04/31/2003". If date has a different format, convert it to "mm/dd/yyyy".
Here is a text:
"""

#Get location
get_location_pr = """You are a geology expert and you are very good in understanding mining reports. You will be given a mining report and you need to extract a location of the mine.
Return a location of the mine in geographic coordinates, that include latitude and longitude. Only return geogrpahic coordinates, separated by comma.
If you cannot determine the geographic coordinates, return None.
Here is a text:
"""
#EOF Prompt templates