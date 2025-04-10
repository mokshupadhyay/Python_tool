from flask import Flask, request, render_template, jsonify, send_file
import pdfplumber
import pandas as pd
import os
import re
import shutil
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def extract_pan_from_filename(filename):
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"
    match = re.search(pan_pattern, filename)
    return match.group(0) if match else None

def extract_total_amount_paid(text):
    total_pattern = r"Summary of payment[\s\S]*?Total \(Rs\.\)\s+([\d,]+\.\d{2})"
    match = re.search(total_pattern, text)
    return float(match.group(1).replace(',', '')) if match else None

def extract_total_tds(text):
    tds_pattern = r"Q1\s+\w+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})"
    match = re.search(tds_pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    backup_pattern = r"Total \(Rs\.\)\s+([\d,]+\.\d{2})"
    matches = re.finditer(backup_pattern, text)
    for i, m in enumerate(matches):
        if i == 1:
            return float(m.group(1).replace(',', ''))
    return None

def process_pdf(pdf_path, deal_name):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() + "\n" for page in pdf.pages if page.extract_text())
            return {
                "PAN of deductee": extract_pan_from_filename(os.path.basename(pdf_path)),
                "Total Amount paid": extract_total_amount_paid(text),
                "Total TDS": extract_total_tds(text),
                "Name of deal": deal_name
            }
    except Exception as e:
        return None

def process_directory(base_dir):
    data = []
    for deal_folder in os.listdir(base_dir):
        deal_path = os.path.join(base_dir, deal_folder)
        if not os.path.isdir(deal_path):
            continue
        for filename in os.listdir(deal_path):
            if filename.endswith('.pdf'):
                result = process_pdf(os.path.join(deal_path, filename), deal_folder)
                if result:
                    data.append(result)
    return data

def download_drive_folder(link, local_dir):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    folder_id = link.split("id=")[-1]
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    os.makedirs(local_dir, exist_ok=True)
    for file in file_list:
        file.GetContentFile(os.path.join(local_dir, file['title']))

def save_data_to_csv(data, output_csv):
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
    return output_csv

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        if 'file' in request.files:
            uploaded_file = request.files['file']
            if uploaded_file.filename.endswith('.zip'):
                zip_path = os.path.join(upload_folder, uploaded_file.filename)
                uploaded_file.save(zip_path)
                shutil.unpack_archive(zip_path, upload_folder)
        
        if 'drive_link' in request.form and request.form['drive_link']:
            download_drive_folder(request.form['drive_link'], upload_folder)
        
        output_csv = 'output.csv'
        data = process_directory(upload_folder)
        save_data_to_csv(data, output_csv)
        return send_file(output_csv, as_attachment=True)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
