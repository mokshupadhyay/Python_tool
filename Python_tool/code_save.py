# import pdfplumber
# import pandas as pd
# import os
# import re

# def extract_pan(text):
#     pan_pattern = r"PAN of the deductee\s+([A-Z]{5}\d{4}[A-Z])"
#     match = re.search(pan_pattern, text)
#     return match.group(1) if match else None

# def extract_total_amount_paid(text):
#     total_pattern = r"Summary of payment[\s\S]*?Total \(Rs\.\)\s+([\d,]+\.\d{2})"
#     match = re.search(total_pattern, text)
#     if match:
#         return float(match.group(1).replace(',', ''))
#     return None

# def extract_total_tds(text):
#     # Look for the TDS amount in the quarterly summary section
#     tds_pattern = r"Q1\s+\w+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})"
#     match = re.search(tds_pattern, text)
#     if match:
#         return float(match.group(1).replace(',', ''))
    
#     # Backup pattern: Look for the total in the challan details section
#     backup_pattern = r"Total \(Rs\.\)\s+([\d,]+\.\d{2})"
#     matches = re.finditer(backup_pattern, text)
#     # Get the second occurrence (usually the TDS total)
#     total = None
#     for i, m in enumerate(matches):
#         if i == 1:  # Second occurrence
#             total = float(m.group(1).replace(',', ''))
#             break
#     return total

# def get_deal_name_from_path(pdf_path):
#     # Split the path into components
#     path_parts = pdf_path.split(os.sep)
#     # Look for the deal name folder (it should be the folder containing the PDF)
#     for i in range(len(path_parts)-1, -1, -1):
#         if path_parts[i].endswith('.pdf'):
#             if i > 0:  # Make sure we have a parent folder
#                 return path_parts[i-1]
#     return None

# def process_pdf(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         text = ""
#         for page in pdf.pages:
#             text += page.extract_text() + "\n"
        
#         pan = extract_pan(text)
#         total_paid = extract_total_amount_paid(text)
#         total_tds = extract_total_tds(text)
#         deal_name = get_deal_name_from_path(pdf_path)
        
#         return {
#             "PAN of deductee": pan,
#             "Total Amount paid": total_paid,
#             "Total TDS": total_tds,
#             "Name of deal": deal_name
#         }

# def main(input_path, output_csv):
#     data = []
#     if os.path.isdir(input_path):
#         for filename in os.listdir(input_path):
#             if filename.endswith(".pdf"):
#                 pdf_path = os.path.join(input_path, filename)
#                 result = process_pdf(pdf_path)
#                 data.append(result)
#     elif os.path.isfile(input_path) and input_path.endswith(".pdf"):
#         result = process_pdf(input_path)
#         data.append(result)
#     else:
#         raise ValueError("Input path is invalid.")
    
#     df = pd.DataFrame(data)
#     df.to_csv(output_csv, index=False)
#     print(f"Data saved to {output_csv}")

# if __name__ == "__main__":
#     input_path = "/Users/mokshupadhyay/Documents/TDS Data of SDI Deals/FY 2024-25 Q1/AAVISHKAAR SEPTEMBER 2023 TRUST 1/AAACD1461F_Q1_2025-26.pdf"
#     output_csv_file = "/Users/mokshupadhyay/sih/Python_tool/FY 2024-25 Q1.csv"
#     main(input_path, output_csv_file)



import pdfplumber
import pandas as pd
import os
import re

def extract_pan(text):
    pan_pattern = r"PAN of the deductee\s+([A-Z]{5}\d{4}[A-Z])"
    match = re.search(pan_pattern, text)
    return match.group(1) if match else None

def extract_total_amount_paid(text):
    total_pattern = r"Summary of payment[\s\S]*?Total \(Rs\.\)\s+([\d,]+\.\d{2})"
    match = re.search(total_pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def extract_total_tds(text):
    # Look for the TDS amount in the quarterly summary section
    tds_pattern = r"Q1\s+\w+\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})"
    match = re.search(tds_pattern, text)
    if match:
        return float(match.group(1).replace(',', ''))
    
    # Backup pattern: Look for the total in the challan details section
    backup_pattern = r"Total \(Rs\.\)\s+([\d,]+\.\d{2})"
    matches = re.finditer(backup_pattern, text)
    # Get the second occurrence (usually the TDS total)
    total = None
    for i, m in enumerate(matches):
        if i == 1:  # Second occurrence
            total = float(m.group(1).replace(',', ''))
            break
    return total

def process_pdf(pdf_path, deal_name):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            pan = extract_pan(text)
            total_paid = extract_total_amount_paid(text)
            total_tds = extract_total_tds(text)
            
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
    
    # Iterate through all subdirectories in the base directory
    for deal_folder in os.listdir(base_dir):
        deal_path = os.path.join(base_dir, deal_folder)
        
        # Skip if not a directory
        if not os.path.isdir(deal_path):
            continue
            
        # Process all PDFs in the deal folder
        for filename in os.listdir(deal_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(deal_path, filename)
                result = process_pdf(pdf_path, deal_folder)
                if result:
                    data.append(result)
                    print(f"Processed: {deal_folder} - {filename}")
    
    return data

def main(input_dir, output_csv):
    # Process all directories and collect data
    data = process_directory(input_dir)
    
    # Create DataFrame and save to CSV
    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_csv, index=False)
        print(f"\nData saved to {output_csv}")
        print(f"Total records processed: {len(data)}")
    else:
        print("No data was processed")

if __name__ == "__main__":
    input_dir = "/Users/mokshupadhyay/Documents/TDS Data of SDI Deals/FY 2024-25 Q1"
    output_csv_file = "/Users/mokshupadhyay/sih/Python_tool/FY 2024-25 Q1.csv"
    main(input_dir, output_csv_file)