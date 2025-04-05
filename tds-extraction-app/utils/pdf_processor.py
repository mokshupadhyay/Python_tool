import pdfplumber
import pandas as pd
import os
import re

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
            
            pan = extract_pan_from_filename(os.path.basename(pdf_path))  # Extract PAN dynamically
            
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
    for deal_folder in os.listdir(base_dir):
        deal_path = os.path.join(base_dir, deal_folder)
        if not os.path.isdir(deal_path):
            continue
        
        for filename in os.listdir(deal_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(deal_path, filename)
                result = process_pdf(pdf_path, deal_folder)
                if result:
                    data.append(result)
                    print(f"Processed: {deal_folder} - {filename}")
    
    return data