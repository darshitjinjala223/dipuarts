
import os
import sys
import shutil

# Add parent dir to sys.path to allow importing utils_excel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils_excel as xls_gen

# Mock data
challan_data = {
    'challan_no': 'TEST-CH-001',
    'date': '2023-01-01',
    'supplier': 'Test Supplier',
    'supplier_gst': 'GST123',
    'items': [{'material': 'Fabric', 'quantity': 100}]
}

invoice_data = {
    'invoice_no': 'TEST-INV-001',
    'date': '2023-01-01',
    'supplier_name': 'Test Supplier',
    'base_amount': 1000,
    'cgst': 25,
    'sgst': 25,
    'total': 1050,
    'challan_no': 'CH-001'
}

try:
    print("Testing Challan Generation...")
    p1 = xls_gen.generate_challan_excel(challan_data)
    print(f"Success: {p1}")
except Exception as e:
    print(f"Failed Challan: {e}")

try:
    print("Testing Invoice Generation...")
    p2 = xls_gen.generate_invoice_excel(invoice_data)
    print(f"Success: {p2}")
except Exception as e:
    print(f"Failed Invoice: {e}")
