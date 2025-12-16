import database as db
import datetime

# Initialize and ensure tables exist
db.init_db()

# Create dummy supplier/material/challan to link
db.add_supplier("DebugSupp", "Addr", "GST123", "999")
sup = db.get_suppliers().iloc[0]
db.add_material("DebugMat", "Meters")
mat = db.get_materials().iloc[0]

# Add a pending challan
c_no = "CHTEST01"
db.add_challan(c_no, str(datetime.date.today()), int(sup['id']), int(mat['id']), 50.0)
pending = db.get_pending_challans()

if pending.empty:
    print("No pending challans to test with.")
else:
    challan_id = int(pending.iloc[0]['id'])
    print(f"Testing save_invoice with Challan ID: {challan_id}")
    
    # Try saving invoice
    inv_no = f"INVTEST_{datetime.datetime.now().timestamp()}"
    success = db.save_invoice(
        invoice_no=inv_no,
        date=str(datetime.date.today()),
        rate=100.0,
        base=5000.0,
        cgst=125.0,
        sgst=125.0,
        total=5250.0,
        challan_ids=[challan_id]
    )
    
    if success:
        print("SUCCESS: Invoice saved.")
    else:
        print("FAILURE: Invoice save returned False.")
