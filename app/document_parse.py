from datetime import date
import json

class MedTestDataEntry:
    def __init__(self, name, value, unit, ref_range, commentary):
        self.name = name.lower()
        self.value = value.lower()
        self.unit = unit.lower()
        self.ref_range = ref_range.lower()
        self.commentary = commentary.lower()

    def __repr__(self):
        return (f"MedicalTestDataEntry(name={self.name}, value={self.value}" 
                f"unit={self.unit},range={self.ref_range}")


class MedStudyDataEntry:
    def __init__(self, device, result, report, recommendation):
        self.device = device.lower()
        self.result = result.lower()
        self.report = report.lower()
        self.recommendation = recommendation.lower()

    def __repr__(self):
        return (f"MedicalTestDataEntry(device={self.device}, result={self.result}" 
                f"report={self.report},recommendation={self.recommendation}")
    

class Document:
    def __init__(self,data_format="", institution_name="", document_type="", document_date="", data=None):
        self.data_format = data_format
        self.institution_name = institution_name
        self.document_type = document_type
        try:
            self.document_date = date.fromisoformat(document_date)
        except Exception:
            self.document_date = date.today().isoformat() # if no date assume today
        self.data = data if data is not None else []

    @classmethod
    def from_json(cls, json_str):
        """Parse the JSON string"""
        data_dict = json.loads(json_str)
        data_format = data_dict.get("data_format", "")
        
        institution_name = data_dict.get("institution_name", "")
        document_type = data_dict.get("document_type", "")
        document_date = data_dict.get("document_date", "")
        data_list = data_dict.get("data", [])

        if data_format:
            if data_format == "test":
                data_entries = [
                    MedTestDataEntry(
                        entry.get("name", ""),
                        entry.get("value", ""),
                        entry.get("unit", ""),
                        entry.get("range", ""),
                        entry.get("commentary", "")
                    )
                    for entry in data_list
                ]

            if data_format == "study":
                data_entries = [
                    MedStudyDataEntry(
                        entry.get("device", ""),
                        entry.get("result", ""),
                        entry.get("report", ""),
                        entry.get("recommendation", ""),
                    )
                    for entry in data_list
                ]
        
            return cls(data_format, institution_name, document_type, document_date, data_entries)
        else:
            return None
        

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