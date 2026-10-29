#!/usr/bin/env python3
"""
Financial Document Extractor
Extracts structured data from financial documents:
- Bank statements
- Pay stubs
- Tax returns (W-2, 1040, etc.)
"""

import re
from typing import Dict, List
from datetime import datetime
from document_parser import DocumentParser


class FinancialExtractor:
    """
    Extract structured data from financial documents
    """

    def __init__(self):
        self.parser = DocumentParser()

    def detect_document_type(self, text: str) -> str:
        """
        Detect the type of financial document

        Args:
            text: OCR extracted text

        Returns:
            Document type string
        """
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['bank statement', 'account statement', 'checking', 'savings']):
            return 'bank_statement'
        elif any(keyword in text_lower for keyword in ['pay stub', 'payslip', 'earnings statement', 'wage']):
            return 'pay_stub'
        elif any(keyword in text_lower for keyword in ['w-2', 'form 1040', 'tax return', 'internal revenue']):
            return 'tax_document'
        else:
            return 'unknown_financial'

    def extract_bank_statement(self, text: str) -> Dict:
        """
        Extract data from bank statements

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Bank Statement"
        }

        patterns = {
            "account_holder": [
                r'Account\s*Holder[:\s]+([A-Z][A-Za-z\s]+)',
                r'Name[:\s]+([A-Z][A-Za-z\s]+)',
            ],
            "account_number": [
                r'Account\s*(?:Number|No\.?)[:\s]+([X\*\d\-]+\d{4})',
                r'Acct\.?\s*(?:#|No\.?)[:\s]+([X\*\d\-]+\d{4})',
            ],
            "statement_period": [
                r'Statement\s*Period[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*(?:to|-)\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'Period[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*(?:to|-)\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "opening_balance": [
                r'(?:Opening|Beginning)\s*Balance[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "closing_balance": [
                r'(?:Closing|Ending|Current)\s*Balance[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "total_deposits": [
                r'Total\s*(?:Deposits|Credits)[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "total_withdrawals": [
                r'Total\s*(?:Withdrawals|Debits)[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean currency values
                    if field in ['opening_balance', 'closing_balance', 'total_deposits', 'total_withdrawals']:
                        value = value.replace(',', '')
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    data[field] = value
                    break

        return data

    def extract_pay_stub(self, text: str) -> Dict:
        """
        Extract data from pay stubs

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Pay Stub"
        }

        patterns = {
            "employee_name": [
                r'Employee\s*Name[:\s]+([A-Z][A-Za-z\s]+)',
                r'Name[:\s]+([A-Z][A-Za-z\s]+)',
            ],
            "employee_id": [
                r'Employee\s*(?:ID|#)[:\s]+(\d+)',
                r'EMP\s*(?:ID|#)[:\s]+(\d+)',
            ],
            "employer_name": [
                r'Employer[:\s]+([A-Z][A-Za-z\s&,\.]+)',
                r'Company[:\s]+([A-Z][A-Za-z\s&,\.]+)',
            ],
            "pay_period": [
                r'Pay\s*Period[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\s*(?:to|-)\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "pay_date": [
                r'Pay\s*Date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'Date\s*Paid[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "gross_pay": [
                r'Gross\s*(?:Pay|Earnings)[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "net_pay": [
                r'Net\s*Pay[:\s]+\$?([\d,]+\.?\d{0,2})',
                r'Take\s*Home[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "ytd_gross": [
                r'YTD\s*Gross[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "ytd_net": [
                r'YTD\s*Net[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean currency values
                    if 'pay' in field or 'ytd' in field:
                        value = value.replace(',', '')
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    data[field] = value
                    break

        return data

    def extract_tax_document(self, text: str) -> Dict:
        """
        Extract data from tax documents (W-2, 1040, etc.)

        Args:
            text: OCR extracted text

        Returns:
            Dict with extracted data
        """
        data = {
            "document_type": "Tax Document"
        }

        # Detect specific form type
        if 'w-2' in text.lower():
            data["form_type"] = "W-2"
        elif '1040' in text:
            data["form_type"] = "Form 1040"

        patterns = {
            "tax_year": [
                r'(?:Tax\s*Year|Year)[:\s]+(\d{4})',
                r'(\d{4})\s*(?:Tax\s*Return|W-2)',
            ],
            "taxpayer_name": [
                r'Employee\s*Name[:\s]+([A-Z][A-Za-z\s]+)',
                r'Taxpayer\s*Name[:\s]+([A-Z][A-Za-z\s]+)',
            ],
            "ssn": [
                r'(?:SSN|Social\s*Security\s*Number)[:\s]+([\dX\*\-]{9,11})',
            ],
            "wages_tips": [
                r'Wages,\s*tips[:\s]+\$?([\d,]+\.?\d{0,2})',
                r'Box\s*1[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "federal_tax_withheld": [
                r'Federal\s*(?:Income\s*)?Tax\s*Withheld[:\s]+\$?([\d,]+\.?\d{0,2})',
                r'Box\s*2[:\s]+\$?([\d,]+\.?\d{0,2})',
            ],
            "employer_name": [
                r'Employer[:\s]+([A-Z][A-Za-z\s&,\.]+)',
                r'Box\s*c[:\s]+([A-Z][A-Za-z\s&,\.]+)',
            ],
            "employer_ein": [
                r'(?:EIN|Employer\s*ID)[:\s]+([\d\-]+)',
                r'Box\s*b[:\s]+([\d\-]+)',
            ],
        }

        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean currency values
                    if any(keyword in field for keyword in ['wages', 'tax', 'withheld']):
                        value = value.replace(',', '')
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    data[field] = value
                    break

        return data

    def extract(self, file_path: str) -> Dict:
        """
        Main extraction method for financial documents

        Args:
            file_path: Path to financial document (PDF or image)

        Returns:
            Dict with extracted financial data
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
        if doc_type == 'bank_statement':
            extracted_data = self.extract_bank_statement(text)
        elif doc_type == 'pay_stub':
            extracted_data = self.extract_pay_stub(text)
        elif doc_type == 'tax_document':
            extracted_data = self.extract_tax_document(text)
        else:
            extracted_data = {
                "document_type": "Unknown Financial Document"
            }

        return {
            "success": True,
            "source_file": file_path,
            "document_category": "financial",
            "detected_type": doc_type,
            "data": extracted_data,
            "raw_text": text
        }


def main():
    """
    Command-line interface for financial document extraction
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract data from financial documents")
    parser.add_argument("file", help="Path to financial document (PDF or image)")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    extractor = FinancialExtractor()
    result = extractor.extract(args.file)

    if result["success"]:
        print(f"✓ Financial document extracted successfully")
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
