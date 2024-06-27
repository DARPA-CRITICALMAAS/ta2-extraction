# Critical Maas Demo

## Description
This document runs through different mining reports to extract desirable summary information on Mineral Deposits and Mineral Resources. 

## How to set up Environment
1. Create virtual environment
2. `pip install -r requirements.txt`

## How to Test Parallel Code
1. Go to parallel_extraction.ipynb
2. Update File Names, Url List, Commodity, Commodity Sign, folder path, output path
3. Run that Cell

## How To Test Non Parallel Code
1. Start virtual environment `source venv/bin/activate`
2. Run python command with correct headers: python extract_commodities_demo.py --pdf_p "PATH/TO/PDF" --pdf_name  "NAME.pdf" --primary_commodity commodity --element_sign commodity_sign

python extract_commodities_demo.py --pdf_p "./reports/mvt_zinc/" --pdf_name  "Bleiberg Pb Zn 5-2017.pdf" --primary_commodity commodity --element_sign commodity_sign