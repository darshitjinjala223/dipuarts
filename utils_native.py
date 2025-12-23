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
    except Exception as e:
        return False, str(e)

def convert_with_libreoffice(input_xlsx, output_pdf):
    """
    Converts Excel to PDF using LibreOffice (Linux/Cloud).
    Requires 'libreoffice' to be installed (via packages.txt).
    """
    input_abs = os.path.abspath(input_xlsx)
    out_dir = os.path.dirname(os.path.abspath(output_pdf))
    
    # Command: soffice --headless --convert-to pdf <input> --outdir <output_dir>
    # Note: LibreOffice uses the same basename. If output_pdf name differs, we might need rename.
    # But usually we generate [name].xlsx -> [name].pdf so it matches automatically.
    
    # Determine Command
    soffice_cmd = 'soffice'
    
    # On macOS, check if soffice is in path, else use full path
    if os.path.exists("/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        soffice_cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        
    cmd = [
        soffice_cmd, 
        '--headless', 
        '--convert-to', 
        'pdf', 
        input_abs, 
        '--outdir', 
        out_dir
    ]
    
    try:
        # TIMEOUT is critical as soffice can hang
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Check if file created
        # LibreOffice uses input filename with .pdf extension
        base_name = os.path.splitext(os.path.basename(input_xlsx))[0]
        expected_pdf = os.path.join(out_dir, f"{base_name}.pdf")
        
        if os.path.exists(expected_pdf):
            # If the requested output name is different, rename it
            if os.path.abspath(output_pdf) != os.path.abspath(expected_pdf):
                os.rename(expected_pdf, output_pdf)
            return True, output_pdf
        else:
            return False, f"LibreOffice failed: {result.stderr or result.stdout}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: LibreOffice took too long."
    except FileNotFoundError:
        return False, "LibreOffice not found. Ensure 'libreoffice' is in packages.txt"
    except Exception as e:
        return False, str(e)
