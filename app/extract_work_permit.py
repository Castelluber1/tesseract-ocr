#!/usr/bin/env python3
"""
Work Permit / Visa Extractor
Extracts structured data from work permits, visas, and employment authorization documents
"""

import re
from typing import Dict
from document_parser import DocumentParser


class WorkPermitExtractor:
    """
    Extract structured data from work permits and visa documents
    """

    def __init__(self):
        self.parser = DocumentParser()

    def detect_permit_type(self, text: str) -> str:
        """
        Detect the type of work authorization document

        Args:
            text: OCR extracted text

        Returns:
            Document type string
        """
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['work permit', 'employment authorization', 'ead']):
            return 'work_permit'
        elif any(keyword in text_lower for keyword in ['h-1b', 'h1b', 'visa']):
            return 'visa'
        elif 'green card' in text_lower or 'permanent resident' in text_lower:
            return 'permanent_resident_card'
        else:
            return 'unknown_work_auth'

    def extract_work_permit(self, text: str) -> Dict:
        """
        Extract data from work permit documents

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Work Permit"
        }

        patterns = {
            "permit_number": [
                r'Permit\s*(?:Number|No\.?|#)[:\s]+([A-Z0-9\-]+)',
                r'Card\s*(?:Number|No\.?|#)[:\s]+([A-Z0-9\-]+)',
            ],
            "full_name": [
                r'Name[:\s]+([A-Z][A-Za-z\s,]+)',
                r'(?:First|Given)\s*Name[:\s]+([A-Z][A-Za-z\s]+).*(?:Last|Family)\s*Name[:\s]+([A-Z][A-Za-z\s]+)',
            ],
            "date_of_birth": [
                r'(?:Date\s*of\s*Birth|DOB)[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'Birth\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "nationality": [
                r'Nationality[:\s]+([A-Z]{3}|[A-Za-z\s]+)',
                r'Country\s*of\s*Citizenship[:\s]+([A-Z]{3}|[A-Za-z\s]+)',
            ],
            "issue_date": [
                r'(?:Issue|Issued)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "expiry_date": [
                r'(?:Expiry|Expiration|Valid\s*Until)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "employer": [
                r'Employer[:\s]+([A-Z][A-Za-z\s&,\.]+)',
                r'Sponsored\s*by[:\s]+([A-Z][A-Za-z\s&,\.]+)',
            ],
            "job_title": [
                r'(?:Job\s*Title|Position|Occupation)[:\s]+([A-Za-z\s,]+)',
            ],
            "work_location": [
                r'(?:Work\s*Location|Place\s*of\s*Employment)[:\s]+([A-Za-z\s,]+)',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data[field] = match.group(1).strip()
                    break

        return data

    def extract_visa(self, text: str) -> Dict:
        """
        Extract data from visa documents

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Visa"
        }

        patterns = {
            "visa_type": [
                r'(?:Visa\s*Type|Class)[:\s]+([A-Z0-9\-]+)',
                r'(H-1B|L-1|O-1|TN|E-2|E-3)',
            ],
            "visa_number": [
                r'Visa\s*(?:Number|No\.?|#)[:\s]+([A-Z0-9]+)',
                r'Control\s*(?:Number|No\.?|#)[:\s]+([A-Z0-9]+)',
            ],
            "full_name": [
                r'Name[:\s]+([A-Z][A-Za-z\s,]+)',
            ],
            "passport_number": [
                r'Passport\s*(?:Number|No\.?|#)[:\s]+([A-Z0-9]+)',
            ],
            "nationality": [
                r'Nationality[:\s]+([A-Z]{3}|[A-Za-z\s]+)',
            ],
            "date_of_birth": [
                r'(?:Date\s*of\s*Birth|DOB)[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "issue_date": [
                r'(?:Issue|Issued)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "expiry_date": [
                r'(?:Expiry|Expiration)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "entries": [
                r'Entries[:\s]+(Multiple|Single|[\d]+)',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data[field] = match.group(1).strip()
                    break

        return data

    def extract(self, file_path: str) -> Dict:
        """
        Main extraction method for work authorization documents

        Args:
            file_path: Path to work permit/visa document (PDF or image)

        Returns:
            Dict with extracted data
        """
        # Parse document with OCR
        parsed = self.parser.parse_document(file_path)

        if not parsed["success"]:
            return {
                "success": False,
                "error": parsed.get("error")
            }

        text = parsed["text"]

        # Detect document type
        doc_type = self.detect_permit_type(text)

        # Extract based on type
        if doc_type in ['work_permit', 'permanent_resident_card']:
            extracted_data = self.extract_work_permit(text)
        elif doc_type == 'visa':
            extracted_data = self.extract_visa(text)
        else:
            extracted_data = {
                "document_type": "Unknown Work Authorization"
            }

        return {
            "success": True,
            "source_file": file_path,
            "document_category": "work_authorization",
            "detected_type": doc_type,
            "data": extracted_data,
            "raw_text": text
        }


def main():
    """
    Command-line interface for work permit extraction
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract data from work permits and visas")
    parser.add_argument("file", help="Path to work authorization document (PDF or image)")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    extractor = WorkPermitExtractor()
    result = extractor.extract(args.file)

    if result["success"]:
        print(f"✓ Work authorization document extracted successfully")
        print(f"Detected Type: {result['detected_type']}")
        print("\nExtracted Data:")
        print(json.dumps(result["data"], indent=2))

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Saved to: {args.output}")
    else:
        print(f"✗ Error: {result.get('error')}")


if __name__ == "__main__":
    main()
