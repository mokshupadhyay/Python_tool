from flask import Flask, request, render_template, send_file, jsonify
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename
import json
from utils.pdf_processor import process_directory

app = Flask(__name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files():
    # Create temporary directories
    input_temp = tempfile.mkdtemp()
    output_temp = tempfile.mkdtemp()
    
    try:
        # Get the files from the request
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400
        
        # Save uploaded files to temp directory preserving directory structure
        for file in files:
            if file.filename and allowed_file(file.filename):
                # Get the relative path of the file
                relative_path = file.filename
                
                # Create the full path in the temp directory
                file_path = os.path.join(input_temp, relative_path)
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save the file
                file.save(file_path)
        
        # Process the files
        output_csv = os.path.join(output_temp, 'tds_data_output.csv')
        data = process_directory(input_temp)
        
        if not data:
            return jsonify({'error': 'No data could be extracted from the PDFs'}), 400
            
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(output_csv, index=False)
        
        # Return the CSV file
        return send_file(
            output_csv,
            mimetype='text/csv',
            as_attachment=True,
            download_name='tds_data_output.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up temp directories
        shutil.rmtree(input_temp, ignore_errors=True)
        shutil.rmtree(output_temp, ignore_errors=True)

@app.route('/status', methods=['GET'])
def status():
    # This is a simple endpoint to check if the server is running
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
