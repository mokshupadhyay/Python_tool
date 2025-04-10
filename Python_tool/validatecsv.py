import pandas as pd
import re

def is_valid_pan(pan):
    """Check if PAN is in a valid format (5 letters, 4 digits, 1 letter)."""
    pan_pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    return bool(re.match(pan_pattern, str(pan)))

def validate_csv(csv_file):
    df = pd.read_csv(csv_file)
    
    errors = []
    
    for index, row in df.iterrows():
        pan = row.get("PAN of deductee", "")
        total_paid = row.get("Total Amount paid", 0)
        total_tds = row.get("Total TDS", 0)
        
        row_errors = []
        
        # Check PAN format
        if not is_valid_pan(pan):
            row_errors.append("Invalid PAN format")
        
        # Check for missing values
        if pd.isna(total_paid) or pd.isna(total_tds):
            row_errors.append("Missing total paid or total TDS")
        
        # Check for negative values
        if total_paid < 0 or total_tds < 0:
            row_errors.append("Negative values found")
        
        # Check logical consistency
        if total_tds > total_paid:
            row_errors.append("TDS cannot be greater than total amount paid")
        
        if row_errors:
            errors.append({"Row": index + 1, "Errors": row_errors})
    
    if errors:
        print("Validation Errors Found:")
        for error in errors:
            print(f"Row {error['Row']}: {', '.join(error['Errors'])}")
    else:
        print("CSV Data is Valid!")

if __name__ == "__main__":
    csv_path = "/Users/mokshupadhyay/sih/Python_tool/FY 2024-25 Q3.csv"
    validate_csv(csv_path)