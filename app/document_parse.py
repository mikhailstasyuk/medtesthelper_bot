import json
import re

class DataEntry:
    def __init__(self, name, value, unit, ref_range):
        self.name = name
        self.value = float(re.sub(r'[^0-9.]', '', value))
        self.unit = unit
        self.ref_range = ref_range
        self.is_normal = self.calculate_is_normal()

    def calculate_is_normal(self):
        """Calculate if value is within reference range"""
        if self.ref_range:
            try:
                min_val, max_val = map(float, self.ref_range.split('-'))
                return min_val <= self.value <= max_val
            except ValueError:
                return False
        return False

    def __repr__(self):
        return (f"DataEntry(name={self.name}, value={self.value}, unit={self.unit}, "
                f"range={self.ref_range}, is_normal={self.is_normal})")


class Document:
    def __init__(self, institution_name="", document_type="", document_date="", data=None):
        self.institution_name = institution_name
        self.document_type = document_type
        self.document_date = document_date
        self.data = data if data is not None else []

    @classmethod
    def from_json(cls, json_str):
        """Parse the JSON string"""
        data_dict = json.loads(json_str)
        
        institution_name = data_dict.get("institution_name", "")
        document_type = data_dict.get("document_type", "")
        document_date = data_dict.get("document_date", "")
        
        data_list = data_dict.get("data", [])
        data_entries = [
            DataEntry(
                entry.get("name", ""),
                entry.get("value", ""),
                entry.get("unit", ""),
                entry.get("range", ""),
            )
            for entry in data_list
        ]
        
        return cls(institution_name, document_type, document_date, data_entries)

    def __repr__(self):
        return (f"Document(institution_name={self.institution_name}, document_type={self.document_type}, "
                f"document_date={self.document_date}, data={self.data})")


if __name__ == "__main__":
    # Example usage
    json_data = """
    {
        "institution_name": "Health Clinic",
        "document_type": "Blood Test",
        "document_date": "2024-09-17",
        "data": [
            {
                "name": "Hemoglobin", 
                "value": "13.5", 
                "unit": "g/dL", 
                "range": "12.0-15.5" 
            },
            {
                "name": "Cholesterol", 
                "value": "190", 
                "unit": "mg/dL", 
                "range": "125-200" 
            }
        ]
    }
    """
    document = Document.from_json(json_data)
    print(document)