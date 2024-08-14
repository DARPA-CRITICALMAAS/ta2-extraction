"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
def created_document_ref(title, url):
    return f"""{{
              "title": "{title}",
              "doi" : "{url}"
              "authors": "[]",
              "year": "",
              "month": "",
              "volume": "",
              "issue": "",
              "description": ""
            }}"""
            
            
def create_mineral_site(url, doc_name):
    return f"""
        {{
            "MineralSite": [
                {{
                    "source_id": "{url}",
                    "record_id": "1",
                    "name": "{doc_name}",
                    "location_info": {{
                        "location": "POINT()",
                        "crs": "",
                        "country": "",
                        "state_or_province": ""
                    }}
                }}
            ]
        }}
        """
        
def create_deposit_format():
    return """
        {"deposit_type": []
        }
        """
        
def create_deposit_format_correct():
    return """
        {
        "deposit_type": {
            "observed text": "https://minmod.isi.edu/resource/deposit_id",  
            "observed text" : "https://minmod.isi.edu/resource/deposit_id",
            "observed text": ""
        }
        }
        """
        
def create_mineral_extractions_format(commodity):
    return f"""
        {{ "extractions":[
        {{
        "Table": "",
        "category": "",
        "zone": "",
        "{commodity} Cut-Off": "",
        "{commodity} Cut-Off Unit": "",
        "{commodity} Tonnage": "",
        "{commodity} Tonnage Unit": "",
        "{commodity} Grade Percent": ""
        }}
        ]
    }}
"""

def create_inventory_format(commodities_dict, commodity, document_dict, doc_date):
        return {
    "commodity": "https://minmod.isi.edu/resource/" + commodities_dict[commodity],
    "category": "",
    "ore": {
        "ore_unit": "",
        "ore_value": ""
    },
    "grade": {
        "grade_unit": "",
        "grade_value": ""
    },
    "cutoff_grade": {
        "grade_unit": "",
        "grade_value": ""
    },
    "contained_metal": "", 
    "reference": {
        "document": document_dict,
        "page_info": [
            {
            "page": ""    
            }
        ]
    },
    "date": doc_date,
    "zone": "",
}
    