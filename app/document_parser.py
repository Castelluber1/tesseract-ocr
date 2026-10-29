#!/usr/bin/env python3
"""
Document Parser - Main OCR and Text Extraction Tool
Handles both PDF and image files, extracts text using OCR
Part of the WAT Framework for immigration document processing
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    import cv2
    import numpy as np
    from PyPDF2 import PdfReader
except ImportError as e:
    print(f"Error: Missing required library. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)


class DocumentParser:
    """
    OCR-based document parser for extracting text from PDFs and images
    """

    def __init__(self, tesseract_path: Optional[str] = None, poppler_path: Optional[str] = None):
        """
        Initialize the document parser

        Args:
            tesseract_path: Path to tesseract executable (if not in PATH)
            poppler_path: Path to poppler bin directory (if not in PATH)
        """
        # Auto-detect Tesseract on Windows if not provided
        if not tesseract_path:
            # Check common Windows installation paths
            windows_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for path in windows_paths:
                if os.path.exists(path):
                    tesseract_path = path
                    break

        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Auto-detect Poppler on Windows if not provided
        if not poppler_path:
            # Check common Windows installation paths
            current_dir = Path(__file__).parent
            poppler_paths = [
                current_dir / "poppler-24.08.0" / "Library" / "bin",  # Local installation
                r"C:\Program Files\poppler\Library\bin",
                r"C:\Program Files (x86)\poppler\Library\bin",
                r"C:\poppler\Library\bin",
            ]
            for path in poppler_paths:
                path_str = str(path) if isinstance(path, Path) else path
                if os.path.exists(path_str):
                    poppler_path = path_str
                    print(f"[INFO] Found Poppler at: {poppler_path}")
                    break

        self.poppler_path = poppler_path

        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            print("WARNING: Tesseract OCR not found!")
            print("Please install Tesseract:")
            print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("  Mac: brew install tesseract")
            print("  Linux: sudo apt-get install tesseract-ocr")
            raise e

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results

        Applies:
        - Grayscale conversion
        - Noise reduction
        - Contrast enhancement (CLAHE)
        - Adaptive thresholding

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image
        """
        # Convert PIL to OpenCV format
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Upscale image for better OCR (2x)
        height, width = gray.shape
        gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

        # Denoise first
        gray = cv2.fastNlMeansDenoising(gray, h=10)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Apply adaptive thresholding for better text recognition
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Morphological operations to clean up text
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

        # Convert back to PIL
        return Image.fromarray(processed)

    def extract_text_from_image(self, image_path: str, preprocess: bool = True) -> Dict:
        """
        Extract text from an image file using OCR

        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess the image

        Returns:
            Dict with extracted text and metadata
        """
        try:
            print(f"[DEBUG] Opening image: {image_path}")
            image = Image.open(image_path)

            if preprocess:
                print(f"[DEBUG] Preprocessing image...")
                image = self.preprocess_image(image)

            # Extract text with detailed data
            print(f"[DEBUG] Running OCR on image (max 120s timeout)...")
            text = pytesseract.image_to_string(image, timeout=120)
            print(f"[DEBUG] OCR complete, extracted {len(text)} chars")
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, timeout=120)

            return {
                "success": True,
                "source": image_path,
                "type": "image",
                "text": text,
                "structured_data": data,
                "page_count": 1
            }

        except Exception as e:
            print(f"[ERROR] Image OCR failed: {str(e)}")
            return {
                "success": False,
                "source": image_path,
                "error": str(e)
            }

    def extract_text_from_pdf(self, pdf_path: str, use_ocr: bool = True, max_pages: int = 5) -> Dict:
        """
        Extract text from a PDF file
        First tries to extract text directly, then falls back to OCR if needed

        Args:
            pdf_path: Path to PDF file
            use_ocr: Whether to use OCR if direct extraction fails
            max_pages: Maximum number of pages to process (default 5 to find bio page)

        Returns:
            Dict with extracted text and metadata
        """
        try:
            # Try direct text extraction first (for digital PDFs)
            print(f"[DEBUG] Opening PDF: {pdf_path}")
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            print(f"[DEBUG] PDF has {num_pages} pages, will process first {min(max_pages, num_pages)} pages")

            all_text = []
            all_structured_data = []

            # Only process first max_pages (passport data is always in first few pages)
            pages_to_process = min(max_pages, num_pages)

            for page_num, page in enumerate(reader.pages[:pages_to_process], 1):
                print(f"[DEBUG] Processing page {page_num}/{pages_to_process}")
                text = page.extract_text()

                # If no text or very little text, use OCR
                if use_ocr and (not text or len(text.strip()) < 50):
                    print(f"[DEBUG] Page {page_num} has little/no text, using OCR...")
                    # Convert PDF page to image and OCR it
                    convert_kwargs = {
                        'pdf_path': pdf_path,
                        'first_page': page_num,
                        'last_page': page_num
                    }
                    if self.poppler_path:
                        convert_kwargs['poppler_path'] = self.poppler_path

                    print(f"[DEBUG] Converting page {page_num} to image...")
                    images = convert_from_path(**convert_kwargs)
                    print(f"[DEBUG] Conversion complete, got {len(images) if images else 0} images")

                    if images:
                        print(f"[DEBUG] Preprocessing image for page {page_num}...")
                        preprocessed = self.preprocess_image(images[0])
                        print(f"[DEBUG] Running OCR on page {page_num} (max 120s timeout)...")
                        text = pytesseract.image_to_string(preprocessed, timeout=120)
                        print(f"[DEBUG] OCR complete for page {page_num}, extracted {len(text)} chars")
                        structured = pytesseract.image_to_data(
                            preprocessed,
                            output_type=pytesseract.Output.DICT,
                            timeout=120
                        )
                        all_structured_data.append(structured)
                else:
                    print(f"[DEBUG] Page {page_num} has digital text ({len(text)} chars)")

                all_text.append(text)

            return {
                "success": True,
                "source": pdf_path,
                "type": "pdf",
                "text": "\n\n--- PAGE BREAK ---\n\n".join(all_text),
                "pages": all_text,
                "structured_data": all_structured_data if all_structured_data else None,
                "page_count": num_pages
            }

        except Exception as e:
            return {
                "success": False,
                "source": pdf_path,
                "error": str(e)
            }

    def parse_document(self, file_path: str, max_pages: int = 5) -> Dict:
        """
        Main parsing method - detects file type and extracts text

        Args:
            file_path: Path to document (PDF or image)
            max_pages: Maximum number of PDF pages to process (default 5 to find bio page)

        Returns:
            Dict with extracted text and metadata
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        extension = path.suffix.lower()

        # Handle PDFs
        if extension == '.pdf':
            return self.extract_text_from_pdf(str(path), max_pages=max_pages)

        # Handle images
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self.extract_text_from_image(str(path))

        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {extension}"
            }

    def save_results(self, results: Dict, output_dir: str = ".tmp") -> str:
        """
        Save parsing results to a JSON file

        Args:
            results: Results dictionary from parse_document
            output_dir: Directory to save results

        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)

        source_name = Path(results.get("source", "unknown")).stem
        output_path = os.path.join(output_dir, f"{source_name}_parsed.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return output_path


def main():
    """
    Example usage and testing
    """
    import argparse

    parser = argparse.ArgumentParser(description="Parse documents using OCR")
    parser.add_argument("file", help="Path to document (PDF or image)")
    parser.add_argument("--tesseract-path", help="Path to tesseract executable")
    parser.add_argument("--output", default=".tmp", help="Output directory")
    parser.add_argument("--no-preprocess", action="store_true",
                       help="Skip image preprocessing")

    args = parser.parse_args()

    # Initialize parser
    doc_parser = DocumentParser(tesseract_path=args.tesseract_path)

    # Parse document
    print(f"Parsing: {args.file}")
    results = doc_parser.parse_document(args.file)

    if results["success"]:
        print(f"\n✓ Successfully parsed {results['page_count']} page(s)")
        print(f"\nExtracted text preview (first 500 chars):")
        print("-" * 80)
        print(results["text"][:500])
        print("-" * 80)

        # Save results
        output_path = doc_parser.save_results(results, args.output)
        print(f"\n✓ Results saved to: {output_path}")
    else:
        print(f"\n✗ Error: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
