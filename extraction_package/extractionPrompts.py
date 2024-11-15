"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""

TOC_ex = """10.2 Analytical Procedures .......................................................................................37
10.3 Quality Control Procedures (QA/QC)...............................................................37
10.4 Sample Security ................................................................................................37
10.5 ISO 9000 Certification ...................................................................................... 38
11.0 DATA
11.1 Historical Data V erification .............................................................................. 38
VERIFICATION...............................................................................................38
12.0 ADJACENT PROPERTIES .........................................................................................38 13.0 MINERAL PROCESSING AND METALLURGICAL TESTING.............................38 14.0 MINERAL RESOURCE AND MINERAL RESERVE ESTIMATES........................39
"""
table_ex = """0.20 1,387,703
MoS2 From
MoS2 To
Volume
Tonnes
SG
Average Grade
Cumulative Tonnes
Cumulative Average Grade
338,810
3.34 0.154
338,810
461,348
3.34 0.256
800,157
275,857
3.34 0.346
1,076,014
280,827
356,842
153,560
3.34 0.450
3.34 0.543
1,510,401
105,624
3.34 0.644
1,616,026
62,685
3.34 0.746
1,678,711
35,725
3,552 11,864 3.34 0.947
3.34 0.840
1,714,435
1,726,299
0.1 0.2
0.2 0.3
0.3 0.4
0.4 0.5
0.5 0.6
0.6 0.7
0.7 0.8
0.8 0.9
0.9 1
Table 19.5: Summary of Inferred MoS2 Mineral Resource.
101,440 138,128 82,592 84,080 45,976 31,624 18,768 10,696
0.154 0.213 0.247 0.289 0.315 0.336 0.352 0.362 0.366"""

find_relevant_commodities = f"""From this text about mineral resources or mineral estimates, extract the commodities and categories from the table. For example, if this is the table: \n {table_ex} \n. The
result should be: {{"commodities": ["Molybdenum"], "categories" : ["Inferred"]}}. Note the categories can be found in the table or in the surrounding text. If there are no commodities or no categories, leave the list empty. Here is the given text: \n
"""

extract_rows_from_tables = """From the given text, create a python dictionary that
extracts the raw data from each of the rows from the __TABLE_NAME__ for each commdity in this list __COMMODITY_LIST__ that describe mineral resource or reserve estimate data. 
Do not duplicate row information.

Here is the given text: \n
"""

find_relevant_table_instructions = f""" Based on the text given, are there tables that describes mineral estimates and mineral resources. These tables should have column names that describe categories, tonnage, cut off grade, or grades. Do not include tables that talk about a mineral resource's sensitivities or that discuss drilling hole metrics,
or any text that discuss mineral resources not in table format. Return the Table Names, Table Years, and commodities found in each table. Note that the phrases mineral estimates and mineral resources are typically in the name.
Here is the text: \n
"""

classifier_prompt = f"""Based on the attached text, can you identify if there is a 
table present, or a list of names that indicate who prepared the document, or if this text shows a Table of Contents page, which typically has a page number, header, or section, or if this text contains the Deposit Types section.

Here is a good example of what a table might look like: \n {table_ex} \n
Here is a good example of what a Table of Contents page looks like: \n {TOC_ex} \n
Here is the text : \n    
"""
find_deposit_types = "Based on the given text, can you extract the list of deposit types that are physically found and relevant to the mining site."

DocRefprompt = "From the attached text, extract description information about the name of the mining site, list of author names (ignore professional titles), year and month it was published, document information such as issue, description, and volume. Also extract location information such as state, country and latitude/longitude. Any unknown values can be left empty. Here is the text: \n"