import os
import re
import pandas as pd
import pdfplumber
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import shutil
from zipfile import ZipFile

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Configure upload folder - use tmp directory for cloud hosting
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(tempfile.gettempdir(), 'uploads'))
OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(tempfile.gettempdir(), 'output'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

def extract_pan_from_filename(filename):
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"
    match = re.search(pan_pattern, filename)
    return match.group(0) if match else None

def extract_total_amount_paid(text):
    total_pattern = r"Summary of payment[\s\S]*?Total \(Rs\.\)\s+([\d,]+\.\d{2})"
    match = re.search(total_pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def extract_total_tds(text):
    tds_pattern = r"Q1\s+\w+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})"
    match = re.search(tds_pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    
    backup_pattern = r"Total \(Rs\.\)\s+([\d,]+\.\d{2})"
    matches = re.finditer(backup_pattern, text)
    total = None
    for i, m in enumerate(matches):
        if i == 1:
            total = float(m.group(1).replace(',', ''))
            break
    return total

def process_pdf(pdf_path, deal_name):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() + "\n" for page in pdf.pages if page.extract_text())
            
            total_paid = extract_total_amount_paid(text)
            total_tds = extract_total_tds(text)
            
            pan = extract_pan_from_filename(os.path.basename(pdf_path))
            
            return {
                "PAN of deductee": pan,
                "Total Amount paid": total_paid,
                "Total TDS": total_tds,
                "Name of deal": deal_name
            }
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return None

def process_directory(base_dir):
    data = []
    processed_count = 0
    errors = []
    
    # Find all PDF files in any subdirectory structure
    for root, dirs, files in os.walk(base_dir):
        # Check if this is a deal directory (has PDF files)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            # Use the parent directory name as the deal name
            deal_name = os.path.basename(root)
            
            for filename in pdf_files:
                pdf_path = os.path.join(root, filename)
                try:
                    result = process_pdf(pdf_path, deal_name)
                    if result:
                        data.append(result)
                        processed_count += 1
                        print(f"Processed: {deal_name}/{filename}")
                    else:
                        errors.append(f"Could not extract data from {deal_name}/{filename}")
                except Exception as e:
                    errors.append(f"Error processing {deal_name}/{filename}: {str(e)}")
    
    return data, processed_count, errors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'tds_zip' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['tds_zip']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.zip'):
        # Clear previous uploads
        for f in os.listdir(app.config['UPLOAD_FOLDER']):
            path = os.path.join(app.config['UPLOAD_FOLDER'], f)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        
        # Create temp file for the zip
        _, temp_path = tempfile.mkstemp()
        file.save(temp_path)
        
        # Extract the zip
        with ZipFile(temp_path, 'r') as zip_ref:
            zip_ref.extractall(app.config['UPLOAD_FOLDER'])
        
        # Remove the temp file
        os.remove(temp_path)
        
        return jsonify({"message": "Uploaded and extracted successfully"}), 200
    
    return jsonify({"error": "Invalid file format, please upload a ZIP file"}), 400

@app.route('/process', methods=['POST'])
def process_files():
    quarter = request.form.get('quarter', 'Unknown Quarter')
    
    data, processed_count, errors = process_directory(app.config['UPLOAD_FOLDER'])
    
    if data:
        df = pd.DataFrame(data)
        output_filename = f"{quarter}.csv"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        df.to_csv(output_path, index=False)
        
        return jsonify({
            "success": True,
            "message": f"Processed {processed_count} files successfully",
            "filename": output_filename,
            "count": processed_count,
            "errors": errors if errors else None
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "No data was processed. Check if your files are in the correct format.",
            "errors": errors if errors else ["No PDF files found with readable data"]
        }), 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True,
        download_name=filename
    )

@app.route('/debug', methods=['GET'])
def debug_folder_structure():
    """Endpoint to help diagnose folder structure issues"""
    structure = []
    
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        level = root.replace(app.config['UPLOAD_FOLDER'], '').count(os.sep)
        indent = ' ' * 4 * level
        folder = os.path.basename(root)
        structure.append(f"{indent}{folder}/")
        
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            structure.append(f"{sub_indent}{f}")
    
    return jsonify({
        "upload_folder": app.config['UPLOAD_FOLDER'],
        "structure": structure
    })

@app.route('/health')
def health_check():
    """Simple health check endpoint for cloud providers"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)