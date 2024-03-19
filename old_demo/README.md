# Critical Maas Demo

## Description
This document runs through different mining reports to extract desirable summary information on Mineral Deposits and Mineral Resources. 

## How To Run
1. Start virtual environment `source venv/bin/activate`
2. Run python command with correct headers: python extract_commodities_demo.py --pdf_p "PATH/TO/PDF" --pdf_name  "NAME.pdf" --primary_commodity commodity --element_sign commodity_sign

python extract_commodities_demo.py --pdf_p "./reports/mvt_zinc/" --pdf_name  "Bleiberg Pb Zn 5-2017.pdf" --primary_commodity commodity --element_sign commodity_sign