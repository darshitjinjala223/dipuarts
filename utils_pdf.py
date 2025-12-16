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
        pass

    def draw_invoice_template(self):
        """Draws the invoice layout manually (borders, lines, headers) if no image."""
        self.set_line_width(0.3)
        self.set_draw_color(0)
        self.set_text_color(0)
        
        # Outer Border
        self.rect(10, 10, 190, 277)
        
        # Header Section
        self.line(10, 40, 200, 40) # Below Title
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 15)
        self.cell(190, 10, "TAX INVOICE", align="C", border=0)
        
        # Details Box
        self.line(10, 90, 200, 90) # Below Order/Challan details
        
        # Left/Right Vertical Split (Header)
        self.line(105, 40, 105, 90) 
        
        # Labels for Header
        self.set_font("Helvetica", "B", 10)
        
        # Right Side Labels
        self.text(107, 45, "Invoice No:")
        self.text(107, 55, "Invoice Date:")
        self.text(107, 65, "Challan No:")
        self.text(107, 75, "Order No:")
        
        # Buyer Section
        self.line(10, 140, 200, 140) # Below Buyer Details
        self.text(12, 95, "Bill To (Buyer):")
        
        # Item Table Header
        self.line(10, 150, 200, 150) # End of Header Row
        self.text(12, 147, "Sr.")
        self.text(25, 147, "Description of Goods")
        self.text(100, 147, "Meters")
        self.text(115, 147, "Rate")
        self.text(135, 147, "Taxable")
        self.text(155, 147, "CGST+SGST")
        self.text(182, 147, "Total")
        
        # Vertical Lines for Table
        # Sr | Desc | Mtr | Rate | Taxable | Tax | Total
        col_x = [20, 95, 112, 130, 150, 175]
        for x in col_x:
            self.line(x, 140, x, 220) # Down to totals
            
        # Bottom Section
        self.line(10, 220, 200, 220) # End of Items
        
        # Footer Totals Layout
        self.line(130, 230, 200, 230)
        self.line(130, 240, 200, 240)
        
        self.set_font("Helvetica", "", 10)
        self.text(132, 225, "Taxable Value:")
        self.text(132, 235, "CGST + SGST:")
        self.text(132, 245, "Grand Total:")
        
        self.set_font("Helvetica", "B", 10)
        self.text(12, 230, "Amount In Words:")

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
    
    # If no background image, draw manual lines
    if not template_path:
        pdf.draw_invoice_template()
    
    if show_grid:
        pdf.draw_grid()
    
    # Text Configuration
    pdf.set_font("Helvetica", size=10) # Reduced base size slightly as there are many fields
    
    # ---------------------------------------------------------
    # USER PROVIDED COORDINATES (DEFAULTS)
    # ---------------------------------------------------------
    # Adjusted defaults to align with manual grid
    defaults = {
        "inv_date": (135, 55),  # Aligned to R-Side Box
        "invoice_no": (135, 45),
        "challan_no": (135, 65),
        "order_no": (135, 75),
        
        "buyer_name": (15, 100),
        "buyer_address": (15, 105),
        "buyer_gst": (15, 130),
        
        # Table Row (Y=155 start)
        "sr_no": (12, 155),
        "item_desc": (25, 155),
        "mtr": (100, 155),
        "rate": (118, 155),
        "taxable_val": (135, 155),
        # gst_rate skipped in manual col
        "gst_amt": (158, 155),
        "row_total": (180, 155),
        
        # Bottom Section
        "taxable_val_btm": (180, 224),
        "amount_words": (45, 230), 
        "cgst_amt": (180, 234), # Manual lines at 230, 240
        "sgst_amt": (180, 238), # squeeze
        "grand_total": (180, 246)
    }
    
    # Merge defaults with user config if provided
    config = defaults.copy()
    if layout_config:
        config.update(layout_config)
    
    # Helper to draw text at config key
    def draw(key, text, bold=False, align="L"):
        # Special keys handling
        if key not in config: return
            
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
    
    # 1.1 Invoice No (New)
    draw("invoice_no", invoice_data.get('invoice_no', ''))

    # 2. Challan No
    draw("challan_no", invoice_data['challan_no'])
    
    # 4. Order No
    draw("order_no", invoice_data.get('order_no', ''))
    
    # 6. Buyer Name
    draw("buyer_name", invoice_data['supplier_name'], bold=True)
    
    # 7. Address
    x, y = config["buyer_address"]
    pdf.set_xy(x, y)
    if not show_grid:
        pdf.multi_cell(80, 5, str(invoice_data.get('supplier_address', '')))
    
    # 8. GSTIN
    draw("buyer_gst", f"GSTIN: {invoice_data.get('supplier_gst', '')}")
    
    # 9. Sr No (Sequential) - TABLE HEADER / LOOP
    # Table Config
    y_start = 155
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
