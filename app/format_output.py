#!/usr/bin/env python3
"""
Output Formatter
Formats extracted document data into JSON and Markdown for immigration forms
"""

import json
import os
from typing import Dict, List
from datetime import datetime
from pathlib import Path


class OutputFormatter:
    """
    Format extracted data into JSON and Markdown outputs
    """

    def __init__(self, output_dir: str = ".tmp"):
        """
        Initialize the output formatter

        Args:
            output_dir: Directory to save formatted outputs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def format_json(self, extracted_data: Dict, pretty: bool = True) -> str:
        """
        Format extracted data as JSON

        Args:
            extracted_data: Dict with extracted document data
            pretty: Whether to pretty-print the JSON

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(extracted_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(extracted_data, ensure_ascii=False)

    def format_markdown(self, extracted_data: Dict) -> str:
        """
        Format extracted data as Markdown for human review
        Shows ONLY the extracted data fields, no system metadata

        Args:
            extracted_data: Dict with extracted document data

        Returns:
            Markdown string with only extracted fields
        """
        md = []

        data = extracted_data.get("data", {})

        # Show only extracted data, no system info
        if not data:
            md.append("Nenhum dado foi extraído do documento.\n")
        else:
            for field, value in data.items():
                if value is not None and value != "":
                    # Format field name
                    field_name = field.replace('_', ' ').title()

                    # Format value
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:,.2f}" if isinstance(value, float) else str(value)
                    else:
                        formatted_value = str(value)

                    md.append(f"**{field_name}:** {formatted_value}\n")

        return "".join(md)

    def format_immigration_form_ready(self, extracted_data: Dict) -> Dict:
        """
        Format extracted data specifically for immigration form filling
        Organizes data with standard field mappings

        Args:
            extracted_data: Dict with extracted document data

        Returns:
            Dict formatted for immigration forms
        """
        form_data = {
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "source_file": extracted_data.get("source_file"),
                "document_category": extracted_data.get("document_category"),
                "document_type": extracted_data.get("detected_type"),
            },
            "personal_information": {},
            "document_details": {},
            "financial_information": {},
            "employment_information": {},
            "education_information": {}
        }

        data = extracted_data.get("data", {})

        # Map fields to appropriate sections
        personal_fields = ["full_name", "first_name", "last_name", "surname", "given_names",
                          "date_of_birth", "sex", "nationality", "place_of_birth"]

        document_fields = ["passport_number", "permit_number", "visa_number", "certificate_id",
                          "issue_date", "expiry_date", "issuing_country", "document_type"]

        financial_fields = ["gross_pay", "net_pay", "ytd_gross", "ytd_net", "opening_balance",
                           "closing_balance", "total_deposits", "total_withdrawals", "wages_tips",
                           "federal_tax_withheld"]

        employment_fields = ["employer", "employer_name", "employer_ein", "job_title",
                            "work_location", "pay_period", "pay_date"]

        education_fields = ["degree_title", "major", "major_field", "institution_name",
                           "graduation_date", "gpa", "total_credits", "certificate_title"]

        # Populate sections
        for field, value in data.items():
            if field in personal_fields:
                form_data["personal_information"][field] = value
            elif field in document_fields:
                form_data["document_details"][field] = value
            elif field in financial_fields:
                form_data["financial_information"][field] = value
            elif field in employment_fields:
                form_data["employment_information"][field] = value
            elif field in education_fields:
                form_data["education_information"][field] = value
            else:
                # Put other fields in document_details as fallback
                form_data["document_details"][field] = value

        # Remove empty sections
        form_data = {k: v for k, v in form_data.items() if v and (not isinstance(v, dict) or v)}

        return form_data

    def save_outputs(self, extracted_data: Dict, base_filename: str = None) -> Dict[str, str]:
        """
        Save extracted data in both JSON and Markdown formats

        Args:
            extracted_data: Dict with extracted document data
            base_filename: Base name for output files (without extension)

        Returns:
            Dict with paths to saved files
        """
        # Determine base filename
        if not base_filename:
            source_file = extracted_data.get("source_file", "extracted_data")
            base_filename = Path(source_file).stem

        # Format outputs
        json_data = self.format_immigration_form_ready(extracted_data)
        md_data = self.format_markdown(extracted_data)

        # Save files
        json_path = os.path.join(self.output_dir, f"{base_filename}_extracted.json")
        md_path = os.path.join(self.output_dir, f"{base_filename}_extracted.md")

        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(self.format_json(json_data))

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_data)

        return {
            "json": json_path,
            "markdown": md_path
        }

    def combine_multiple_documents(self, extracted_docs: List[Dict]) -> Dict:
        """
        Combine data from multiple extracted documents into a single output

        Args:
            extracted_docs: List of extracted document dicts

        Returns:
            Combined data dict formatted for immigration forms
        """
        combined = {
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "total_documents": len(extracted_docs),
                "documents": []
            },
            "personal_information": {},
            "document_details": [],
            "financial_information": {},
            "employment_information": {},
            "education_information": {}
        }

        for doc in extracted_docs:
            # Add to document list
            combined["metadata"]["documents"].append({
                "source_file": doc.get("source_file"),
                "category": doc.get("document_category"),
                "type": doc.get("detected_type")
            })

            # Format and merge data
            formatted = self.format_immigration_form_ready(doc)

            # Merge sections (personal info gets merged, others get appended)
            if "personal_information" in formatted:
                combined["personal_information"].update(formatted["personal_information"])

            if "document_details" in formatted and formatted["document_details"]:
                combined["document_details"].append(formatted["document_details"])

            if "financial_information" in formatted:
                if not combined["financial_information"]:
                    combined["financial_information"] = formatted["financial_information"]
                else:
                    # Append financial docs as separate entries
                    if "financial_documents" not in combined["financial_information"]:
                        combined["financial_information"]["financial_documents"] = []
                    combined["financial_information"]["financial_documents"].append(
                        formatted["financial_information"]
                    )

            if "employment_information" in formatted:
                combined["employment_information"].update(formatted["employment_information"])

            if "education_information" in formatted:
                combined["education_information"].update(formatted["education_information"])

        # Clean up empty sections
        combined = {k: v for k, v in combined.items() if v and (not isinstance(v, dict) or v)}

        return combined


def main():
    """
    Command-line interface for output formatting
    """
    import argparse

    parser = argparse.ArgumentParser(description="Format extracted document data")
    parser.add_argument("input", help="Path to extracted data JSON file")
    parser.add_argument("--output-dir", default=".tmp", help="Output directory")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both",
                       help="Output format")

    args = parser.parse_args()

    # Load input data
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Format and save
    formatter = OutputFormatter(output_dir=args.output_dir)
    saved_files = formatter.save_outputs(data)

    print("✓ Formatted outputs saved:")
    for format_type, path in saved_files.items():
        print(f"  - {format_type.upper()}: {path}")


if __name__ == "__main__":
    main()
