import streamlit as st
import pandas as pd
from datetime import date
import database as db
import utils_pdf as pdf_gen

# Page Config
st.set_page_config(page_title="Auto Biller", page_icon="🧾", layout="wide")

# Initialize DB
if 'db_init' not in st.session_state:
    db.init_db()
    st.session_state['db_init'] = True

st.title("🧾 Auto Biller")

# Sidebar Navigation
menu = st.sidebar.radio("Menu", ["Dashboard", "New Inward (Challan)", "Settings", "PDF Layout"])

if menu == "PDF Layout":
    st.header("📏 PDF Layout Adjustment")
    st.info("Adjust coordinates (X, Y) for all fields.")
    
    # ---------------------------------------------------------
    # INTERACTIVE CALIBRATION UI
    # ---------------------------------------------------------
    
    # 1. Initialize Layout Config in Session State if not present
    if 'layout_config' not in st.session_state:
        # Default starting points
        st.session_state['layout_config'] = {
            "inv_date": (40, 69), "challan_no": (170, 64), "challan_date": (170, 69),
            "order_no": (170, 75), "order_date": (170, 82), "buyer_name": (40, 98),
            "buyer_address": (40, 105), "buyer_gst": (40, 115),
            "sr_no": (10, 145), "item_desc": (30, 145), "mtr": (102, 145),
            "rate": (115, 145), "taxable_val": (135, 145), "gst_rate": (150, 145),
            "gst_amt": (160, 145), "row_total": (180, 145),
            "taxable_val_btm": (180, 224), "cgst_amt": (180, 228), "sgst_amt": (180, 235),
            "grand_total": (180, 242), "amount_words": (20, 225)
        }

    layout = st.session_state['layout_config']

    # 2. UI Controls
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("1. Select Field")
        field_options = list(layout.keys())
        selected_field = st.radio("Field to Move:", field_options, horizontal=False)
        
        step_size = st.select_slider("Movement Step (mm):", options=[1, 5, 10], value=5)

    with c2:
        st.subheader("2. Move it!")
        current_x, current_y = layout[selected_field]
        
        st.markdown(f"**Current Position:** X={current_x}, Y={current_y}")
        
        # Arrow Keys Layout
        #    [  Up  ]
        # [L]      [R]
        #    [ Down ]
        
        col_mid = st.columns(3)
        if col_mid[1].button("⬆️ Up"):
            layout[selected_field] = (current_x, current_y - step_size)
            st.rerun()
            
        col_lr = st.columns(3)
        if col_lr[0].button("⬅️ Left"):
            layout[selected_field] = (current_x - step_size, current_y)
            st.rerun()
            
        if col_lr[2].button("➡️ Right"):
            layout[selected_field] = (current_x + step_size, current_y)
            st.rerun()
            
        col_bot = st.columns(3)
        if col_bot[1].button("⬇️ Down"):
            layout[selected_field] = (current_x, current_y + step_size)
            st.rerun()
            
        st.divider()
        st.subheader("3. Check Result")
        
        # Generate Preview Button (Always available)
        dummy_data = {
            'invoice_no': "INV-001", 'date': "2023-01-01", 
            'supplier_name': "TEST SUPPLIER", 'supplier_address': "123 Test St", 'supplier_gst': "GST123",
            'material': "TEST MATERIAL",
            'challan_no': "CH-001", 'challan_date': "2023-01-01",
            'order_no': "ORD-01", 'order_date': "2023-01-01",
            'qty': 100, 'rate': 10,
            'base_amount': 1000, 'cgst': 25, 'sgst': 25, 'total': 1050
        }
        
        pdf_bytes = pdf_gen.generate_invoice_pdf(dummy_data, layout, show_grid=True)
        st.download_button(
            label="🔄 Regenerate Preview PDF",
            data=bytes(pdf_bytes),
            file_name="Calibration_Preview.pdf",
            mime='application/pdf',
            type="primary"
        )
        st.caption("Click, Download, Check, Repeat.")

    # Save State is automatic via session_state assignment, but let's confirm
    st.session_state['layout_config'] = layout

elif menu == "Settings":
    st.header("Master Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Suppliers")
        with st.form("add_supplier"):
            name = st.text_input("Supplier Name")
            address = st.text_area("Address")
            gst = st.text_input("GST No")
            phone = st.text_input("Phone")
            if st.form_submit_button("Add Supplier"):
                if db.add_supplier(name, address, gst, phone):
                    st.success(f"Supplier {name} added!")
                else:
                    st.error("Error adding supplier (Name might be duplicate).")
        
        # List Suppliers
        suppliers = db.get_suppliers()
        if not suppliers.empty:
            st.dataframe(suppliers[['name', 'gst_no']])

    with col2:
        st.subheader("Raw Materials")
        with st.form("add_material"):
            m_name = st.text_input("Material Name")
            unit = st.text_input("Unit", value="Meters")
            if st.form_submit_button("Add Material"):
                if db.add_material(m_name, unit):
                    st.success(f"Material {m_name} added!")
        
        # List Materials
        materials = db.get_materials()
        if not materials.empty:
            st.dataframe(materials[['name', 'unit']])

elif menu == "New Inward (Challan)":
    st.header("📝 Inward Entry (Challan)")
    
    suppliers = db.get_suppliers()
    materials = db.get_materials()
    
    if suppliers.empty or materials.empty:
        st.warning("Please add Suppliers and Materials in Settings first!")
    else:
        with st.form("challan_form"):
            c_no = st.text_input("Challan No.")
            c_date = st.date_input("Date", value=date.today())
            
            s_options = {row['name']: row['id'] for index, row in suppliers.iterrows()}
            selected_supplier = st.selectbox("Select Supplier", list(s_options.keys()))
            
            m_options = {row['name']: row['id'] for index, row in materials.iterrows()}
            selected_material = st.selectbox("Select Material", list(m_options.keys()))
            
            qty = st.number_input("Quantity (Meters)", min_value=1.0)
            
            submitted = st.form_submit_button("Save Challan")
            
    if submitted:
        if db.add_challan(c_no, str(c_date), s_options[selected_supplier], m_options[selected_material], qty):
            st.success("Challan Saved Successfully!")
            
            # Option to download Challan PDF immediately
            challan_data = {
                'challan_no': c_no,
                'date': str(c_date),
                'supplier': selected_supplier,
                'material': selected_material,
                'quantity': qty
            }
            pdf_bytes = pdf_gen.generate_challan_pdf(challan_data)
            st.download_button("Download Challan PDF", data=bytes(pdf_bytes), file_name=f"Challan_{c_no}.pdf", mime='application/pdf')

elif menu == "Dashboard":
    st.header("📌 Stickering / Pending Bills")
    
    pending = db.get_pending_challans()
    
    if pending.empty:
        st.info("No pending challans found.")
    else:
        # Display as cards (using columns)
        # We'll use an expander or just container for each
        st.write("Select a Challan to Generate Invoice")
        
        for index, row in pending.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
                c1.write(f"**{row['supplier']}**")
                c2.write(f"Mat: {row['material']}")
                c3.write(f"Qty: {row['quantity']}")
                c4.write(f"#: {row['challan_no']}")
                
                if c5.button("Generate Bill", key=f"btn_{row['id']}"):
                    st.session_state['selected_challan'] = row.to_dict()
                    st.rerun()

    # Invoice Generation Section (if a card was clicked)
    if 'selected_challan' in st.session_state:
        st.divider()
        sel = st.session_state['selected_challan']
        st.subheader(f"Generate Invoice for Challan #{sel['challan_no']}")
        
        # Need to fetch full supplier details (address/gst) which might not be in the 'pending' DF
        # Quick look-up based on supplier name in `sel`
        suppliers_df = db.get_suppliers()
        supp_details = suppliers_df[suppliers_df['name'] == sel['supplier']].iloc[0]
        
        with st.form("invoice_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                inv_no = st.text_input("Invoice No")
                inv_date = st.date_input("Invoice Date", value=date.today())
                rate = st.number_input("Rate per Meter", min_value=0.0, step=0.1)
            with col_b:
                order_no = st.text_input("Order No (Manual)")
                order_date = st.date_input("Order Date (Manual)", value=date.today())
            
            # Real-time Calculcation display
            base = sel['quantity'] * rate
            cgst = base * 0.025
            sgst = base * 0.025
            total = base + cgst + sgst
            
            st.markdown(f"**Base Amount:** ₹{base:.2f}")
            st.markdown(f"**Tax (5%):** ₹{cgst+sgst:.2f}")
            st.markdown(f"**Total:** ₹{total:.2f}")
            
            generate_clicked = st.form_submit_button("Confirm & Download PDF")

        if generate_clicked:
            # PDF Generation with custom layout if available
            layout_config = st.session_state.get('layout_config', None)
            
            inv_data = {
                'invoice_no': inv_no,
                'date': str(inv_date),
                'supplier_name': sel['supplier'],
                'supplier_address': supp_details['address'],
                'supplier_gst': supp_details['gst_no'],
                'material': sel['material'],
                'challan_no': sel['challan_no'],
                'challan_date': str(sel['date']), # Added challan date
                'order_no': order_no,
                'order_date': str(order_date),
                'qty': sel['quantity'],
                'rate': rate,
                'base_amount': base,
                'cgst': cgst,
                'sgst': sgst,
                'total': total
            }
            # Pass layout config to PDF gen
            pdf_bytes = pdf_gen.generate_invoice_pdf(inv_data, layout_config)
            
            st.success("Invoice Generated!")
            st.download_button("Download Invoice PDF", data=bytes(pdf_bytes), file_name=f"Invoice_{inv_no}.pdf", mime='application/pdf')
                
                # Ideally, here we would update the DB to mark challan as 'Billed'
                # But for this V1, we just generate the PDF.
