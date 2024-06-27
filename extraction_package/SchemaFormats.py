
def created_document_ref(title):
    return f"""{{
              "title": "{title}",
              "doi" : ""
              "authors": "[]",
              "year": "",
              "month": "",
              "volume": "",
              "issue": "",
              "description": ""
            }}"""
            
            
def create_mineral_site(record_id, doc_name):
    return f"""
                {{
                    "source_id": "",
                    "record_id": "{record_id}",
                    "name": "{doc_name}",
                    "location_info": {{
                        "location": "POINT()",
                        "crs": "",
                        "country": "",
                        "state_or_province": ""
                    }}
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
        "chemical compound": "",
        "{commodity} Cut-Off": "",
        "{commodity} Cut-Off Unit": "",
        "{commodity} Tonnage": "",
        "{commodity} Tonnage Unit": "",
        "{commodity} Grade": "",
        "{commodity} Grade Unit": ""
        }}
        ]
    }}
"""

def create_inventory_format(commodities_dict, commodity, document_dict):
    doc_month = document_dict.get('month', '')
    doc_year = document_dict.get('year', '')
    doc_date = ''
    if doc_month and doc_year:
        doc_date = f"{doc_year}-{doc_month}"

    format = {
    "commodity": "https://minmod.isi.edu/resource/" + commodities_dict[commodity],
    "category": "",
    "material_form": "",
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

    if doc_date:
        return format

    else: 
        format.pop('date')
        return format