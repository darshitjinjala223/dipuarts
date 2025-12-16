from fpdf import FPDF
import os

class PDF(FPDF):
    def __init__(self, background_image=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_image = background_image

    def header(self):
        # If a background image is provided, place it covering the whole page
        if self.background_image and os.path.exists(self.background_image):
            self.image(self.background_image, x=0, y=0, w=210, h=297)

    def draw_grid(self):
        """Draws a detailed 5mm grid for calibration."""
        self.set_font("Helvetica", size=6)
        self.set_text_color(200, 0, 0) # Red
        self.set_draw_color(255, 200, 200) # Light Red for 5mm
        
        # 5mm lines
        for x in range(0, 220, 5):
            self.line(x, 0, x, 297)
        for y in range(0, 310, 5):
            self.line(0, y, 210, y)

        self.set_draw_color(200, 0, 0) # Dark Red for 10mm
        # 10mm lines + Labels
        for x in range(0, 220, 10):
            self.line(x, 0, x, 297)
            self.text(x+1, 3, str(x))
        for y in range(0, 310, 10):
            self.line(0, y, 210, y)
            self.text(1, y-1, str(y))

    def footer(self):
        # Remove footer if using a full page template, or keep page numbers if needed
        # self.set_y(-15)
        # self.set_font('Helvetica', 'I', 8)
        # self.cell(0, 10, f'Page {self.page_no()}', align='C')
        pass

from num2words import num2words

def generate_invoice_pdf(invoice_data, layout_config=None, show_grid=False):
    """
    Generates an invoice PDF using 'BILL FORMAT.png' (or fallback).
    """
    template_path = "invoice_template.png"
    if not os.path.exists(template_path):
        template_path = "BILL FORMAT.png" 
    if not os.path.exists(template_path):
        template_path = None 

    pdf = PDF(background_image=template_path)
    pdf.add_page()
    
    if show_grid:
        pdf.draw_grid()
    
    # Text Configuration
    pdf.set_font("Helvetica", size=10) # Reduced base size slightly as there are many fields
    
    # ---------------------------------------------------------
    # USER PROVIDED COORDINATES (DEFAULTS)
    # ---------------------------------------------------------
    defaults = {
        "inv_date": (40, 69),
        "challan_no": (170, 64),
        "challan_date": (170, 69),
        "order_no": (170, 75),
        "order_date": (170, 82),
        "buyer_name": (40, 98),
        "buyer_address": (40, 105),
        "buyer_gst": (40, 115),
        
        # Table Row (Y=145)
        "sr_no": (10, 145),
        "item_desc": (30, 145),
        "mtr": (102, 145),
        "rate": (115, 145),
        "taxable_val": (135, 145),
        "gst_rate": (150, 145),
        "gst_amt": (160, 145),
        "row_total": (180, 145),
        
        # Bottom Section
        "taxable_val_btm": (180, 224),
        "amount_words": (20, 225), # Using X=20 start for better wrap space
        "cgst_amt": (180, 228),
        "sgst_amt": (180, 235),
        "grand_total": (180, 242)
    }
    
    # Merge defaults with user config if provided
    config = defaults.copy()
    if layout_config:
        config.update(layout_config)

    # Helper to draw text at config key
    def draw(key, text, bold=False, align="L"):
        if key in config:
            x, y = config[key]
            pdf.set_xy(x, y)
            if bold: pdf.set_font("Helvetica", "B", 10)
            else: pdf.set_font("Helvetica", "", 10)
            
            if show_grid:
                pdf.set_text_color(0, 0, 255)
                pdf.cell(50, 10, f"[{key}]", border=0, align=align)
                pdf.set_text_color(0)
            else:
                pdf.cell(50, 10, str(text), border=0, align=align)

    # 1. Invoice Date
    draw("inv_date", invoice_data['date'])
    
    # 2. Challan No
    draw("challan_no", invoice_data['challan_no'])
    
    # 3. Challan Date (Same as entry date)
    draw("challan_date", invoice_data.get('challan_date', ''))
    
    # 4. Order No
    draw("order_no", invoice_data.get('order_no', ''))
    
    # 5. Order Date
    draw("order_date", invoice_data.get('order_date', ''))
    
    # 6. Buyer Name
    draw("buyer_name", invoice_data['supplier_name'], bold=True)
    
    # 7. Address
    # Multi-line handling for address? For now simply placing it.
    # We might need set_xy then multi_cell if address is long.
    x, y = config["buyer_address"]
    pdf.set_xy(x, y)
    if not show_grid:
        pdf.multi_cell(100, 5, str(invoice_data.get('supplier_address', '')))
    
    # 8. GSTIN
    draw("buyer_gst", invoice_data.get('supplier_gst', ''))
    
    # 9. Sr No (Sequential) - TABLE HEADER / LOOP
    # Table Config
    y_start = 145
    row_height = 8 # mm
    
    items = invoice_data.get('items', [])
    if not items:
        # Fallback for old single-item structure
        items = [{
            'material': invoice_data.get('material', ''),
            'qty': invoice_data.get('qty', 0),
            'rate': invoice_data.get('rate', 0),
            'base_amount': invoice_data.get('base_amount', 0),
            'cgst': invoice_data.get('cgst', 0),
            'sgst': invoice_data.get('sgst', 0),
            'total': invoice_data.get('total', 0)
        }]
        
    for i, item in enumerate(items):
        current_y = y_start + (i * row_height)
        
        # Determine Rate/Tax/Total if not pre-calculated in item dict 
        # (utils_excel logic suggests item dict has keys: material, qty, rate, base_amount, cgst, sgst, total)
        # We rely on 'item' having these.
        
        # 9. Sr No
        pdf.set_xy(config["sr_no"][0], current_y)
        pdf.cell(10, 10, str(i + 1), align="C")
        
        # 10. Item Description
        pdf.set_xy(config["item_desc"][0], current_y)
        pdf.cell(70, 10, str(item.get('material', '')))
        
        # 11. MTR (Quantity)
        pdf.set_xy(config["mtr"][0], current_y)
        pdf.cell(15, 10, str(item.get('qty', 0)), align="C")
        
        # 12. Rate
        pdf.set_xy(config["rate"][0], current_y)
        pdf.cell(20, 10, f"{item.get('rate', 0):.2f}", align="C")
        
        # 13. Taxable Value (Row)
        pdf.set_xy(config["taxable_val"][0], current_y)
        pdf.cell(15, 10, f"{item.get('base_amount', 0):.2f}", align="R")
        
        # 14. GST Rate
        pdf.set_xy(config["gst_rate"][0], current_y)
        pdf.cell(10, 10, "5%", align="C")
        
        # 15. GST Amount (Row)
        row_gst = item.get('cgst', 0) + item.get('sgst', 0)
        pdf.set_xy(config["gst_amt"][0], current_y)
        pdf.cell(20, 10, f"{row_gst:.2f}", align="R")
        
        # 16. Total (Row)
        pdf.set_xy(config["row_total"][0], current_y)
        pdf.cell(20, 10, f"{item.get('total', 0):.2f}", align="R")

    
    # --- Bottom Section ---
    
    # 13b. Taxable Value (Bottom)
    draw("taxable_val_btm", f"{invoice_data['base_amount']:.2f}", align="R")
    
    # 17. CGST Amount
    draw("cgst_amt", f"{invoice_data['cgst']:.2f}", align="R")
    
    # 18. SGST Amount
    draw("sgst_amt", f"{invoice_data['sgst']:.2f}", align="R")
    
    # 16b / 19. Grand Total
    draw("grand_total", f"{invoice_data['total']:.2f}", align="R")
    
    # 19. Amount in Words
    width_for_words = 110 - 10 # approximate based on user request x-10 to x-110
    total_val = invoice_data['total']
    try:
        words = num2words(total_val, lang='en_IN').title() + " Only"
    except:
        words = f"{total_val} Only" # Fallback
        
    x, y = config["amount_words"]
    pdf.set_xy(x, y)
    if show_grid:
        pdf.set_text_color(0, 0, 255)
        pdf.cell(100, 10, "[Amount In Words]", border=0)
    else:
        pdf.multi_cell(100, 5, f"Rupees {words}")

    return pdf.output()

def generate_challan_pdf(challan_data):
    """
    Generates a delivery challan PDF using 'challan_template.png'.
    """
    template_path = "challan_template.png"
    if not os.path.exists(template_path):
        template_path = None

    pdf = PDF(background_image=template_path)
    pdf.add_page()
    
    pdf.set_font("Helvetica", size=12)
    
    # Challan No & Date
    pdf.set_xy(150, 40)
    pdf.cell(50, 10, f"{challan_data['challan_no']}", border=0)
    
    pdf.set_xy(150, 48)
    pdf.cell(50, 10, f"{challan_data['date']}", border=0)
    
    # Supplier / Delivered To
    pdf.set_xy(25, 55)
    pdf.set_font("Helvetica", "B", 14)
    # Handle multi-line address if needed by just putting Name
    # Data often comes as {supplier: name} or {supplier_name: ..}
    # Check calling code consistency. utils_excel uses 'supplier'.
    pdf.cell(100, 10, f"{challan_data.get('supplier', '')}", border=0)
    
    # Table Content
    y_start = 100
    row_height = 10
    pdf.set_font("Helvetica", size=12)
    
    items = challan_data.get('items', [])
    if not items:
        # Fallback
        items = [{'material': challan_data.get('material', ''), 'quantity': challan_data.get('quantity', '')}]
    
    for i, item in enumerate(items):
        current_y = y_start + (i * row_height)
        
        pdf.set_xy(25, current_y)
        pdf.cell(100, 10, f"{item.get('material', '')}", border=0)
        
        pdf.set_xy(150, current_y)
        pdf.cell(40, 10, f"{item.get('quantity', '')}", border=0, align="C")
    
    return pdf.output()
