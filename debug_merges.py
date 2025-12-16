import openpyxl

def list_merges(filename):
    wb = openpyxl.load_workbook(filename)
    sheet = wb.active
    print(f"--- Merged Ranges in {filename} ---")
    for range in sheet.merged_cells.ranges:
        print(range)

list_merges("CHALLAN FORMAT.xlsx")
