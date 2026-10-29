#!/usr/bin/env python3
"""
Immigration Document Extraction - Web Interface
Flask web app for uploading and processing immigration documents
"""

import os
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import extraction tools
from extract_passport import PassportExtractor
from extract_financial import FinancialExtractor
from extract_work_permit import WorkPermitExtractor
from extract_education import EducationExtractor
from format_output import OutputFormatter

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = '.tmp'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize extractors
extractors = {
    'passport': PassportExtractor(),
    'financial': FinancialExtractor(),
    'work_permit': WorkPermitExtractor(),
    'education': EducationExtractor()
}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and extraction"""

    # Check if files were uploaded
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')
    document_type = request.form.get('document_type', 'passport')

    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400

    results = []

    for file in files:
        if file and allowed_file(file.filename):
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Extract data based on document type
                extractor = extractors.get(document_type)
                if not extractor:
                    return jsonify({'error': f'Invalid document type: {document_type}'}), 400

                print(f"\n[DEBUG] Extracting {filename} as {document_type}...")
                extracted_data = extractor.extract(filepath)
                print(f"[DEBUG] Extraction result: success={extracted_data.get('success')}")

                # Format output
                formatter = OutputFormatter(output_dir=OUTPUT_FOLDER)
                output_files = formatter.save_outputs(extracted_data, base_filename=Path(filename).stem)
                print(f"[DEBUG] Output files: {output_files}")

                # Read the markdown content
                markdown_content = ""
                if output_files and 'markdown' in output_files:
                    try:
                        with open(output_files['markdown'], 'r', encoding='utf-8') as f:
                            markdown_content = f.read()
                        print(f"[DEBUG] Markdown content length: {len(markdown_content)} chars")
                    except Exception as e:
                        print(f"[DEBUG] Error reading markdown: {e}")
                        markdown_content = f"Erro ao ler markdown: {str(e)}"
                else:
                    print(f"[DEBUG] No markdown file generated")
                    markdown_content = "Nenhum arquivo markdown foi gerado."

                result = {
                    'filename': filename,
                    'success': extracted_data.get('success', False),
                    'data': extracted_data.get('data', {}),
                    'document_category': extracted_data.get('document_category'),
                    'detected_type': extracted_data.get('detected_type'),
                    'extraction_method': extracted_data.get('extraction_method'),
                    'output_files': output_files,
                    'markdown_content': markdown_content
                }

                # If extraction failed, include error
                if not extracted_data.get('success', False):
                    result['error'] = extracted_data.get('error', 'Falha na extração - motivo desconhecido')
                    print(f"[DEBUG] Extraction failed: {result['error']}")

                results.append(result)

                # Clean up uploaded file
                os.remove(filepath)

            except Exception as e:
                error_msg = f"Erro ao processar arquivo: {str(e)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                print(traceback.format_exc())

                results.append({
                    'filename': filename,
                    'success': False,
                    'error': error_msg,
                    'markdown_content': ''
                })
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)

    return jsonify({'results': results})


@app.route('/download/<file_type>/<filename>')
def download_file(file_type, filename):
    """Download extracted JSON or Markdown files"""

    if file_type not in ['json', 'markdown']:
        return jsonify({'error': 'Invalid file type'}), 400

    # Construct file path
    if file_type == 'json':
        filepath = os.path.join(OUTPUT_FOLDER, f"{filename}_extracted.json")
    else:
        filepath = os.path.join(OUTPUT_FOLDER, f"{filename}_extracted.md")

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    return send_file(filepath, as_attachment=True)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'extractors': list(extractors.keys())
    })


@app.route('/api/batch', methods=['POST'])
def batch_process():
    """Process multiple documents and combine results"""

    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')

    all_extractions = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Auto-detect document type or use specified type
                # For now, try all extractors and use the one with most data
                best_result = None
                best_field_count = 0

                for doc_type, extractor in extractors.items():
                    try:
                        result = extractor.extract(filepath)
                        if result.get('success'):
                            field_count = len(result.get('data', {}))
                            if field_count > best_field_count:
                                best_result = result
                                best_field_count = field_count
                    except Exception:
                        continue

                if best_result:
                    all_extractions.append(best_result)

                # Clean up
                os.remove(filepath)

            except Exception as e:
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)

    if all_extractions:
        # Combine all extractions
        formatter = OutputFormatter(output_dir=OUTPUT_FOLDER)
        combined = formatter.combine_multiple_documents(all_extractions)

        # Save combined output
        combined_path = os.path.join(OUTPUT_FOLDER, 'combined_extraction.json')
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)

        return jsonify({
            'success': True,
            'total_documents': len(all_extractions),
            'combined_data': combined,
            'download_url': '/download/json/combined_extraction'
        })

    return jsonify({'error': 'No documents could be processed'}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print("\n" + "="*60)
    print("Immigration Document Extraction Web Interface")
    print("="*60)
    print(f"\nStarting Flask server on port {port} (debug={debug})...")
    print("="*60 + "\n")

    app.run(debug=debug, host='0.0.0.0', port=port)
