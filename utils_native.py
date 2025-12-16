import os
import subprocess
import time

def convert_excel_to_pdf(input_xlsx, output_pdf):
    """
    Converts Excel to PDF using macOS AppleScript + Microsoft Excel.
    Requires Microsoft Excel to be installed.
    """
    input_abs = os.path.abspath(input_xlsx)
    output_abs = os.path.abspath(output_pdf)
    
    # Ensure file exists
    if not os.path.exists(input_abs):
        raise FileNotFoundError(f"Excel file not found: {input_abs}")
        
    # AppleScript to convert
    # Note: 'save workbook as' with 'file format PDF file format'
    
    script = f'''
    tell application "Microsoft Excel"
        set DisplayAlerts to false
        
        try
            open "{input_abs}"
            
            delay 0.5 
            
            -- Coerce path to file object (Fix for -2700)
            set pdfPath to "{output_abs}"
            
            -- Save
            save active workbook in pdfPath as PDF file format
            
            close active workbook saving no
        on error errMsg
            try
                close active workbook saving no
            end try
            error errMsg
        end try
    end tell
    '''
    
    try:
        # Run AppleScript
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"AppleScript Error: {result.stderr}")
            return False, result.stderr
            
        if os.path.exists(output_abs):
            return True, output_abs
        else:
            return False, "PDF file not created."
            
    except subprocess.TimeoutExpired:
        return False, "Timeout: Excel took too long to respond."
    except Exception as e:
        return False, str(e)
