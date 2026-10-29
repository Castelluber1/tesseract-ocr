#!/usr/bin/env python3
"""
Passport Data Extractor
Extracts structured data from passport documents using OCR + rule-based parsing
Supports MRZ (Machine Readable Zone) parsing for standard passports
"""

import re
from typing import Dict, Optional
from datetime import datetime
from document_parser import DocumentParser


class PassportExtractor:
    """
    Extract structured data from passport documents
    """

    def __init__(self):
        self.parser = DocumentParser()

        # MRZ character mapping for check digits
        self.mrz_char_values = {
            **{str(i): i for i in range(10)},
            **{chr(65 + i): 10 + i for i in range(26)},
            '<': 0
        }

    def parse_mrz_line(self, text: str) -> Optional[Dict]:
        """
        Parse Machine Readable Zone (MRZ) from passport

        MRZ Format (Type 3 - standard passport):
        Line 1: P<ISSUINGCOUNTRY<<LASTNAME<<FIRSTNAME<<<<<<<<<<<<<
        Line 2: PASSPORTNUMBER<NATIONALITY<DOB<SEX<EXPIRY<PERSONALNUMBER<CHECK

        Args:
            text: Full OCR text from passport

        Returns:
            Dict with parsed MRZ data or None if MRZ not found
        """
        # Look for MRZ pattern (44 characters, alphanumeric with <)
        lines = text.split('\n')
        mrz_lines = []

        for line in lines:
            # Clean line - remove spaces and keep only valid MRZ chars
            cleaned = re.sub(r'[^A-Z0-9<]', '', line.upper())

            # MRZ lines are typically 44 characters (allow 40-46 for variance)
            if 40 <= len(cleaned) <= 46:
                if cleaned.startswith('P<'):
                    print(f"[DEBUG] Found MRZ Line 1: {cleaned} (len={len(cleaned)})")
                    mrz_lines.append(cleaned)
                elif len(mrz_lines) == 1 and cleaned[0].isalnum():
                    # Second line follows first line
                    print(f"[DEBUG] Found MRZ Line 2: {cleaned} (len={len(cleaned)})")
                    mrz_lines.append(cleaned)

        if len(mrz_lines) < 2:
            print(f"[DEBUG] MRZ not found. Found {len(mrz_lines)} lines.")
            return None

        print(f"[DEBUG] Parsing MRZ with {len(mrz_lines)} lines")

        try:
            line1 = mrz_lines[0]
            line2 = mrz_lines[1]

            # Parse Line 1: P<CTRY<<LASTNAME<<FIRSTNAME
            document_type = line1[0]  # Should be 'P'
            issuing_country = line1[2:5].replace('<', ' ').strip()

            # Extract names
            names_part = line1[5:44].split('<<')
            last_name = names_part[0].replace('<', ' ').strip()
            first_name = names_part[1].replace('<', ' ').strip() if len(names_part) > 1 else ''

            # Parse Line 2
            passport_number = line2[0:9].replace('<', '').strip()
            nationality = line2[10:13].replace('<', ' ').strip()

            # Date of birth (YYMMDD format)
            dob_str = line2[13:19]
            dob = self._parse_mrz_date(dob_str)

            # Sex
            sex = line2[20]

            # Expiry date (YYMMDD format)
            expiry_str = line2[21:27]
            expiry = self._parse_mrz_date(expiry_str)

            # Personal number (optional)
            personal_number = line2[28:42].replace('<', '').strip()

            return {
                "document_type": "Passport",
                "passport_number": passport_number,
                "last_name": last_name,
                "first_name": first_name,
                "full_name": f"{first_name} {last_name}".strip(),
                "nationality": nationality,
                "issuing_country": issuing_country,
                "date_of_birth": dob,
                "sex": sex,
                "expiry_date": expiry,
                "personal_number": personal_number if personal_number else None,
                "mrz_found": True
            }

        except Exception as e:
            print(f"Error parsing MRZ: {e}")
            return None

    def _parse_mrz_date(self, date_str: str) -> Optional[str]:
        """
        Parse MRZ date format (YYMMDD) to YYYY-MM-DD

        Args:
            date_str: Date in YYMMDD format

        Returns:
            Date in YYYY-MM-DD format or None
        """
        try:
            if not date_str or len(date_str) != 6:
                return None

            yy = int(date_str[0:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:6])

            # Determine century (assume dates > 50 are 1900s, else 2000s)
            year = 1900 + yy if yy > 50 else 2000 + yy

            date_obj = datetime(year, mm, dd)
            return date_obj.strftime("%Y-%m-%d")

        except Exception:
            return None

    def extract_from_text(self, text: str) -> Dict:
        """
        Extract passport data from OCR text using pattern matching

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted passport information
        """
        print(f"\n[DEBUG] === OCR TEXT START ===\n{text}\n[DEBUG] === OCR TEXT END ===\n")

        data = {
            "document_type": "Passport",
            "mrz_found": False
        }

        # Try MRZ parsing first (most reliable for core fields)
        mrz_data = self.parse_mrz_line(text)
        if mrz_data:
            data.update(mrz_data)

        # ALWAYS try pattern matching to extract additional fields
        # (even if MRZ was found, to get fields like place_of_birth, date_of_issue, etc.)
        # Pattern matching for ALL passport fields
        # More flexible patterns to handle OCR errors
        patterns = {
            # Personal Information
            "full_name": [
                r'(?:Name|Nom)[:/\s]+([A-Z][A-Z\s]+?)(?:\n|Nationality|Date)',
            ],
            "surname": [
                r'Surname[:/\s]+([A-Z][A-Z\s]+?)(?:\n|Given|Date|Nationality)',
                r'Last\s*Name[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
                r'Nom[:/\s]+([A-Z][A-Z\s]+?)(?:\n|Pr[ée]nom)',
            ],
            "given_names": [
                r'Given\s*Names?[:/\s]+([A-Z][A-Z\s]+?)(?:\n|Date|Nationality|Sex)',
                r'(?:First|Given)\s*Name[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
                r'Pr[ée]noms?[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
            ],

            # Nationality and Passport Info
            "nationality": [
                r'Nationality[:/\s]+([A-Z]{3})',
                r'Nationality[:/\s]+([A-Z][A-Z\s]+?)(?:\n|Date|Sex)',
                r'Nationalit[ée][:/\s]+([A-Z]{3}|[A-Z\s]+)',
            ],
            "passport_number": [
                r'Passport\s*(?:No|Number|#)[.:/\s]+([A-Z0-9]+)',
                r'No[.:/\s]+([A-Z]\d{7,9})',
                r'Document\s*(?:No|Number)[.:/\s]+([A-Z0-9]+)',
            ],

            # Dates
            "date_of_birth": [
                r'Date\s*of\s*Birth[:/\s]+(\d{1,2}[-/\s]\w{3}[-/\s]\d{4})',
                r'Date\s*of\s*Birth[:/\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'DOB[:/\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Date\s*de\s*naissance[:/\s]+(\d{1,2}[-/\s]\w{3}[-/\s]\d{4})',
            ],
            "date_of_issue": [
                r'Date\s*of\s*Issue[:/\s]+(\d{1,2}[-/\s]\w{3}[-/\s]\d{4})',
                r'Date\s*of\s*Issue[:/\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Issue\s*Date[:/\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Date\s*de\s*d[ée]livrance[:/\s]+(\d{1,2}[-/\s]\w{3}[-/\s]\d{4})',
            ],
            "date_of_expiry": [
                r'Date\s*of\s*Expir[ya][:/\s]+(\d{1,2}[-/\s]\w{3}[-/\s]\d{4})',
                r'Date\s*of\s*Expir[ya][:/\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Expir[ya]\s*Date[:/\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Date\s*d\'expiration[:/\s]+(\d{1,2}[-/\s]\w{3}[-/\s]\d{4})',
            ],

            # Place Information
            "place_of_birth": [
                r'Place\s*of\s*Birth[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|Date|Country)',
                r'Birth\s*Place[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|$)',
                r'Lieu\s*de\s*naissance[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|$)',
                r'City\s*of\s*Birth[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|$)',
            ],
            "place_of_issue": [
                r'Place\s*of\s*Issue[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|Date|Authority)',
                r'Lieu\s*de\s*d[ée]livrance[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|$)',
            ],
            "country_of_birth": [
                r'Country\s*of\s*Birth[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
            ],

            # Authority and Issuing Info
            "authority": [
                r'Authority[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|Date|$)',
                r'Issuing\s*Authority[:/\s]+([A-Z][A-Z\s,]+?)(?:\n|$)',
                r'Autorit[ée][:/\s]+([A-Z][A-Z\s,]+?)(?:\n|$)',
            ],
            "issuing_country": [
                r'Issuing\s*Country[:/\s]+([A-Z]{3})',
                r'Issuing\s*Country[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
            ],

            # Physical Characteristics
            "sex": [
                r'Sex[:/\s]+([MF])',
                r'Gender[:/\s]+([MF])',
                r'Sexe[:/\s]+([MF])',
            ],
            "height": [
                r'Height[:/\s]+(\d+\s*(?:cm|CM|m|M))',
                r'Taille[:/\s]+(\d+\s*(?:cm|CM|m|M))',
            ],
            "eye_color": [
                r'Eye\s*Colo[u]?r[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
                r'Eyes[:/\s]+([A-Z][A-Z\s]+?)(?:\n|$)',
            ],
        }

        for field, pattern_list in patterns.items():
            # Skip if field already exists from MRZ (MRZ data is more reliable)
            if field in data and data[field]:
                continue

            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    # Clean up extracted value
                    value = re.sub(r'\s+', ' ', value)
                    data[field] = value
                    print(f"[DEBUG] Extracted {field}: {value}")
                    break

        return data

    def extract(self, file_path: str) -> Dict:
        """
        Main extraction method for passport documents

        Args:
            file_path: Path to passport image or PDF

        Returns:
            Dict with extracted passport data
        """
        # Parse document with OCR
        print(f"[DEBUG] Starting OCR parsing for: {file_path}")
        parsed = self.parser.parse_document(file_path)
        print(f"[DEBUG] OCR parsing complete, success={parsed['success']}")

        if not parsed["success"]:
            return {
                "success": False,
                "error": parsed.get("error")
            }

        # Extract structured data
        print(f"[DEBUG] Starting data extraction from OCR text...")
        extracted_data = self.extract_from_text(parsed["text"])
        print(f"[DEBUG] Data extraction complete")

        return {
            "success": True,
            "source_file": file_path,
            "document_category": "passport",
            "extraction_method": "MRZ" if extracted_data.get("mrz_found") else "Pattern Matching",
            "data": extracted_data,
            "raw_text": parsed["text"]
        }


def main():
    """
    Command-line interface for passport extraction
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract data from passport documents")
    parser.add_argument("file", help="Path to passport document (PDF or image)")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    extractor = PassportExtractor()
    result = extractor.extract(args.file)

    if result["success"]:
        print("✓ Passport data extracted successfully")
        print(f"Method: {result['extraction_method']}")
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
