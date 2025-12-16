import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "autobiller.db"

def init_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Suppliers Table
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    address TEXT,
                    gst_no TEXT,
                    phone TEXT
                )''')

    # Materials Table
    c.execute('''CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    unit TEXT DEFAULT 'Meters'
                )''')

    # Challans (Inward) Table
    c.execute('''CREATE TABLE IF NOT EXISTS challans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challan_no TEXT NOT NULL,
                    date TEXT NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    material_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    status TEXT DEFAULT 'Pending', -- Pending, Billed
                    invoice_id INTEGER,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                    FOREIGN KEY (material_id) REFERENCES materials (id)
                )''')

    # Invoices (Outward) Table
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    challan_id INTEGER NOT NULL,
                    rate REAL NOT NULL,
                    base_amount REAL NOT NULL,
                    cgst_amount REAL NOT NULL,
                    sgst_amount REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    FOREIGN KEY (challan_id) REFERENCES challans (id)
                )''')

    # Payments Table
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    mode TEXT, -- Cash, Cheque, UPI
                    image_path TEXT,
                    notes TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
                )''')

    conn.commit()
    
    # Schema Migration for Soft Delete
    try:
        c.execute("ALTER TABLE invoices ADD COLUMN is_deleted INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass # Column likely exists
        
    try:
        c.execute("ALTER TABLE invoices ADD COLUMN challan_ids_snapshot TEXT")
        conn.commit()
    except:
        pass # Column likely exists
    
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

# --- CRUD Operations ---

def add_supplier(name, address, gst_no, phone):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO suppliers (name, address, gst_no, phone) VALUES (?, ?, ?, ?)", 
                  (name, address, gst_no, phone))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_suppliers():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM suppliers", conn)
    conn.close()
    return df

def add_material(name, unit):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO materials (name, unit) VALUES (?, ?)", (name, unit))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_materials():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM materials", conn)
    conn.close()
    return df

def add_challan(challan_no, date, supplier_id, material_id, quantity):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO challans (challan_no, date, supplier_id, material_id, quantity) VALUES (?, ?, ?, ?, ?)",
                  (challan_no, date, supplier_id, material_id, quantity))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_pending_challans():
    conn = get_connection()
    query = """
    SELECT c.id, c.challan_no, c.date, s.name as supplier, m.name as material, c.quantity 
    FROM challans c
    JOIN suppliers s ON c.supplier_id = s.id
    JOIN materials m ON c.material_id = m.id
    WHERE c.status = 'Pending'
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def update_challan_quantity(challan_id, new_quantity):
    """Update quantity of a specific challan (used for dashboard edits)."""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE challans SET quantity = ? WHERE id = ?", (new_quantity, challan_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating quantity: {e}")
        return False
    finally:
        conn.close()

def save_invoice(invoice_no, date, rate, base, cgst, sgst, total, challan_ids):
    """Save invoice header and link challans."""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Store snapshot of IDs for restoration possibility
        ids_str = ",".join(map(str, challan_ids))
        
        # 1. Insert Invoice
        c.execute("""INSERT INTO invoices 
                    (invoice_no, date, challan_id, rate, base_amount, cgst_amount, sgst_amount, total_amount, challan_ids_snapshot) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (invoice_no, date, 0, rate, base, cgst, sgst, total, ids_str))
        
        inv_id = c.lastrowid
        
        # 2. Update Challans status and link to invoice
        placeholders = ', '.join(['?'] * len(challan_ids))
        query = f"UPDATE challans SET status = 'Billed', invoice_id = ? WHERE id IN ({placeholders})"
        args = [inv_id] + challan_ids
        c.execute(query, args)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving invoice: {e}")
        return False
    finally:
        conn.close()

# --- READ QUERIES (Excluding Deleted) ---

def get_invoice_history():
    """Fetch active invoices (Excluding Deleted)."""
    conn = get_connection()
    query = """
    SELECT i.id, i.invoice_no, i.date, i.total_amount, i.base_amount, 
           (SELECT count(*) FROM challans c WHERE c.invoice_id = i.id) as challan_count,
           (SELECT s.name FROM suppliers s 
            JOIN challans c ON c.supplier_id = s.id 
            WHERE c.invoice_id = i.id LIMIT 1) as supplier_name
    FROM invoices i
    WHERE (i.is_deleted IS NULL OR i.is_deleted = 0)
    ORDER BY i.id DESC
    """
    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_invoice_details(invoice_id):
    """Fetch all challans associated with an invoice."""
    conn = get_connection()
    query = """
    SELECT c.challan_no, c.date, m.name as material, c.quantity
    FROM challans c
    JOIN materials m ON c.material_id = m.id
    WHERE c.invoice_id = ?
    """
    df = pd.read_sql(query, conn, params=(invoice_id,))
    conn.close()
    return df

def get_supplier_stats(supplier_name):
    """Get total billed amount for a supplier (Excluding Deleted)."""
    conn = get_connection()
    query = """
    SELECT SUM(total_amount) 
    FROM (
        SELECT DISTINCT i.id, i.total_amount
        FROM invoices i
        JOIN challans c ON c.invoice_id = i.id
        JOIN suppliers s ON c.supplier_id = s.id
        WHERE s.name = ? AND (i.is_deleted IS NULL OR i.is_deleted = 0)
    )
    """
    c = conn.cursor()
    c.execute(query, (supplier_name,))
    result = c.fetchone()[0]
    conn.close()
    return result if result else 0.0

def get_supplier_docs(supplier_name):
    """Get lists of invoices and challans for a supplier (Excluding Deleted Invoices)."""
    conn = get_connection()
    
    # Get Invoices
    q_inv = """
    SELECT DISTINCT i.id, i.invoice_no, i.date, i.total_amount, 
           i.rate, i.base_amount, i.cgst_amount, i.sgst_amount
    FROM invoices i
    JOIN challans c ON c.invoice_id = i.id
    JOIN suppliers s ON c.supplier_id = s.id
    WHERE s.name = ? AND (i.is_deleted IS NULL OR i.is_deleted = 0)
    ORDER BY i.date DESC
    """
    invoices = pd.read_sql(q_inv, conn, params=(supplier_name,))
    
    # Get Challans (All)
    q_chal = """
    SELECT c.challan_no, c.date, m.name as material, c.quantity, c.status
    FROM challans c
    JOIN suppliers s ON c.supplier_id = s.id
    JOIN materials m ON c.material_id = m.id
    WHERE s.name = ?
    ORDER BY c.date DESC
    """
    challans = pd.read_sql(q_chal, conn, params=(supplier_name,))
    
    conn.close()
    return invoices, challans

def restore_invoice(invoice_id):
    """Restore a deleted invoice if its challans are still available."""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # 1. Get snapshot IDs
        c.execute("SELECT challan_ids_snapshot FROM invoices WHERE id = ?", (invoice_id,))
        row = c.fetchone()
        if not row or not row[0]:
            print("No snapshot found to restore.")
            return False, "No linked challan data found."
            
        challan_ids = [int(x) for x in row[0].split(',')]
        
        # 2. Check validity (Are any challans already billed in ANOTHER active invoice?)
        # We check if status='Billed' AND invoice_id != this_invoice_id (and invoice_id is not null)
        # But wait, if they were deleted, they are Pending.
        # If they were re-billed, they are Billed.
        
        placeholders = ', '.join(['?'] * len(challan_ids))
        check_q = f"SELECT count(*) FROM challans WHERE id IN ({placeholders}) AND status = 'Billed'"
        c.execute(check_q, challan_ids)
        billed_count = c.fetchone()[0]
        
        if billed_count > 0:
            return False, "Cannot restore: Some associated challans have already been re-billed in a new invoice."
            
        # 3. Restore
        # Link Challans back
        update_q = f"UPDATE challans SET status = 'Billed', invoice_id = ? WHERE id IN ({placeholders})"
        c.execute(update_q, [invoice_id] + challan_ids)
        
        # Set Active
        c.execute("UPDATE invoices SET is_deleted = 0 WHERE id = ?", (invoice_id,))
        
        conn.commit()
        return True, "Invoice restored successfully."
    except Exception as e:
        print(f"Error restoring: {e}")
        return False, str(e)
    finally:
        conn.close()

def delete_invoice(invoice_id):
    """Soft Delete invoice and revert challans to Pending."""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # 1. Revert Challans
        c.execute("UPDATE challans SET status = 'Pending', invoice_id = NULL WHERE invoice_id = ?", (invoice_id,))
        
        # 2. Soft Delete Invoice
        c.execute("UPDATE invoices SET is_deleted = 1 WHERE id = ?", (invoice_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting invoice: {e}")
        return False
    finally:
        conn.close()

# --- PAYMENT FUNCTIONS ---

def add_payment(date, supplier_id, amount, mode, image_path, notes):
    """Record a payment for a supplier."""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO payments (date, supplier_id, amount, mode, image_path, notes) VALUES (?, ?, ?, ?, ?, ?)",
                  (date, supplier_id, amount, mode, image_path, notes))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding payment: {e}")
        return False
    finally:
        conn.close()

def get_supplier_payments(supplier_name):
    """Get all payments for a supplier."""
    conn = get_connection()
    query = """
    SELECT p.id, p.date, p.amount, p.mode, p.image_path, p.notes
    FROM payments p
    JOIN suppliers s ON p.supplier_id = s.id
    WHERE s.name = ?
    ORDER BY p.date DESC
    """
    df = pd.read_sql(query, conn, params=(supplier_name,))
    conn.close()
    return df

def get_supplier_balance(supplier_name):
    """Get Billed, Paid, and Balance for a supplier."""
    billed = get_supplier_stats(supplier_name) # Uses filtered stats
    
    conn = get_connection()
    query = """
    SELECT SUM(p.amount)
    FROM payments p
    JOIN suppliers s ON p.supplier_id = s.id
    WHERE s.name = ?
    """
    c = conn.cursor()
    c.execute(query, (supplier_name,))
    paid = c.fetchone()[0]
    conn.close()
    
    paid = paid if paid else 0.0
    balance = billed - paid
    return billed, paid, balance

# --- MASTER HISTORY ---

def get_master_history():
    """Fetch ALL invoices including Deleted."""
    conn = get_connection()
    query = """
    SELECT i.id, i.invoice_no, i.date, i.total_amount, i.is_deleted,
           (SELECT s.name FROM suppliers s 
            JOIN challans c ON c.supplier_id = s.id 
            WHERE c.invoice_id = i.id LIMIT 1) as supplier_name
    FROM invoices i
    ORDER BY i.id DESC
    """
    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_master_challans():
    """Fetch ALL challans."""
    conn = get_connection()
    query = """
    SELECT c.challan_no, c.date, s.name as supplier, m.name as material, c.quantity, c.status
    FROM challans c
    JOIN suppliers s ON c.supplier_id = s.id
    JOIN materials m ON c.material_id = m.id
    ORDER BY c.date DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df
