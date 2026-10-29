#!/usr/bin/env python3
"""
Education Document Extractor
Extracts structured data from education documents:
- Degrees / Diplomas
- Transcripts
- Certificates
"""

import re
from typing import Dict, List
from document_parser import DocumentParser


class EducationExtractor:
    """
    Extract structured data from education documents
    """

    def __init__(self):
        self.parser = DocumentParser()

    def detect_document_type(self, text: str) -> str:
        """
        Detect the type of education document

        Args:
            text: OCR extracted text

        Returns:
            Document type string
        """
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['transcript', 'academic record', 'grades']):
            return 'transcript'
        elif any(keyword in text_lower for keyword in ['diploma', 'degree', 'bachelor', 'master', 'phd']):
            return 'degree'
        elif any(keyword in text_lower for keyword in ['certificate', 'certification', 'course completion']):
            return 'certificate'
        else:
            return 'unknown_education'

    def extract_degree(self, text: str) -> Dict:
        """
        Extract data from degree/diploma documents

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Degree/Diploma"
        }

        patterns = {
            "student_name": [
                r'(?:This\s*is\s*to\s*certify\s*that|hereby\s*conferred\s*upon)\s+([A-Z][A-Za-z\s,\.]+)',
                r'(?:awarded\s*to|presented\s*to)\s+([A-Z][A-Za-z\s,\.]+)',
                r'Name[:\s]+([A-Z][A-Za-z\s,]+)',
            ],
            "degree_title": [
                r'(?:degree\s*of|conferred\s*the)\s+([A-Za-z\s,]+?)(?:in|from)',
                r'(Bachelor\s*of\s*[A-Za-z\s]+|Master\s*of\s*[A-Za-z\s]+|Doctor\s*of\s*[A-Za-z\s]+)',
                r'(B\.?[AS]\.?|M\.?[AS]\.?|Ph\.?D\.?|MBA)\s+(?:in|degree)',
            ],
            "major_field": [
                r'(?:in|major)\s+([A-Za-z\s]+?)(?:from|has|with)',
                r'Field\s*of\s*Study[:\s]+([A-Za-z\s]+)',
            ],
            "institution_name": [
                r'(?:from|University\s*of|College\s*of)\s+([A-Z][A-Za-z\s,&]+?)(?:has|hereby|located)',
                r'Institution[:\s]+([A-Z][A-Za-z\s,&]+)',
            ],
            "graduation_date": [
                r'(?:Graduation|Conferred|Awarded)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(?:on\s*this|dated)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',  # Month Day, Year
            ],
            "honors": [
                r'(Summa\s*Cum\s*Laude|Magna\s*Cum\s*Laude|Cum\s*Laude|with\s*Honors?)',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data[field] = match.group(1).strip()
                    break

        return data

    def extract_transcript(self, text: str) -> Dict:
        """
        Extract data from transcript documents

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Transcript"
        }

        patterns = {
            "student_name": [
                r'Student\s*Name[:\s]+([A-Z][A-Za-z\s,]+)',
                r'Name[:\s]+([A-Z][A-Za-z\s,]+)',
            ],
            "student_id": [
                r'Student\s*(?:ID|Number|No\.?)[:\s]+([\d\-]+)',
            ],
            "institution_name": [
                r'(?:University|College|Institution)[:\s]+([A-Z][A-Za-z\s,&]+)',
            ],
            "degree_program": [
                r'(?:Program|Degree)[:\s]+([A-Za-z\s,]+)',
                r'(Bachelor\s*of\s*[A-Za-z\s]+|Master\s*of\s*[A-Za-z\s]+)',
            ],
            "major": [
                r'Major[:\s]+([A-Za-z\s]+)',
            ],
            "gpa": [
                r'(?:GPA|Grade\s*Point\s*Average)[:\s]+([\d\.]+)',
                r'Cumulative\s*GPA[:\s]+([\d\.]+)',
            ],
            "graduation_date": [
                r'(?:Graduation|Completion)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'Graduated[:\s]+([A-Z][a-z]+\s+\d{4})',
            ],
            "total_credits": [
                r'Total\s*Credits[:\s]+([\d\.]+)',
                r'Credits\s*Earned[:\s]+([\d\.]+)',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Convert numeric fields
                    if field in ['gpa', 'total_credits']:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    data[field] = value
                    break

        return data

    def extract_certificate(self, text: str) -> Dict:
        """
        Extract data from certificate documents

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Certificate"
        }

        patterns = {
            "recipient_name": [
                r'(?:awarded\s*to|presented\s*to|certifies\s*that)\s+([A-Z][A-Za-z\s,\.]+)',
                r'Name[:\s]+([A-Z][A-Za-z\s,]+)',
            ],
            "certificate_title": [
                r'Certificate\s*(?:of|in)\s+([A-Za-z\s]+)',
                r'Certification\s*in\s+([A-Za-z\s]+)',
            ],
            "issuing_organization": [
                r'(?:issued\s*by|from)\s+([A-Z][A-Za-z\s,&]+)',
                r'Organization[:\s]+([A-Z][A-Za-z\s,&]+)',
            ],
            "issue_date": [
                r'(?:Issue|Issued|Date)\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
            ],
            "expiry_date": [
                r'(?:Expiry|Expiration|Valid\s*Until)[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "certificate_id": [
                r'Certificate\s*(?:ID|Number|No\.?)[:\s]+([A-Z0-9\-]+)',
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
        Main extraction method for education documents

        Args:
            file_path: Path to education document (PDF or image)

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
        doc_type = self.detect_document_type(text)

        # Extract based on type
        if doc_type == 'degree':
            extracted_data = self.extract_degree(text)
        elif doc_type == 'transcript':
            extracted_data = self.extract_transcript(text)
        elif doc_type == 'certificate':
            extracted_data = self.extract_certificate(text)
        else:
            extracted_data = {
                "document_type": "Unknown Education Document"
            }

        return {
            "success": True,
            "source_file": file_path,
            "document_category": "education",
            "detected_type": doc_type,
            "data": extracted_data,
            "raw_text": text
        }


def main():
    """
    Command-line interface for education document extraction
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract data from education documents")
    parser.add_argument("file", help="Path to education document (PDF or image)")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    extractor = EducationExtractor()
    result = extractor.extract(args.file)

    if result["success"]:
        print(f"✓ Education document extracted successfully")
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
