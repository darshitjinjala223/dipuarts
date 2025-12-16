import openpyxl

def inspect_sheet(filename):
    print(f"--- Inspecting {filename} ---")
    wb = openpyxl.load_workbook(filename, data_only=True)
    sheet = wb.active
    
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value:
                print(f"[{cell.coordinate}]: {cell.value}")

inspect_sheet("INVOICE FORMAT2.xlsx")
print("\n")
inspect_sheet("CHALLAN FORMAT.xlsx")
