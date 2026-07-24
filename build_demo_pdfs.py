import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

out_dir = r"c:\dev\github\personal\Reimbursements\demo_docs"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

def make_pdf(filename, image_paths):
    c = canvas.Canvas(os.path.join(out_dir, filename), pagesize=letter)
    for img in image_paths:
        if img:
            c.drawImage(img, 0, 0, width=letter[0], height=letter[1])
        c.showPage()
    c.save()

# Image paths
brain_dir = r"C:\Users\nedpe\.gemini\antigravity\brain\9ca07473-815c-4d16-b6c4-36135fd6196e"
mortgage = os.path.join(brain_dir, "assurance_mortgage_1784859700423.jpg")
entergy = os.path.join(brain_dir, "entergy_bill_1784859707137.jpg")
pool = os.path.join(brain_dir, "pool_invoice_1784859714023.jpg")
school = os.path.join(brain_dir, "stjude_school_1784859720961.jpg")
water = os.path.join(brain_dir, "water_bill_1784859736604.jpg")
medical = os.path.join(brain_dir, "medical_receipt_1784859742298.jpg")
soccer = os.path.join(brain_dir, "soccer_receipt_1784859748199.jpg")

# vol1: mortgage(pg1), entergy(pg2), blank(pg3), water(pg4)
make_pdf("vol1.pdf", [mortgage, entergy, None, water])

# vol2: pool(pg1), blank(pg2), school(pg3)
make_pdf("vol2.pdf", [pool, None, school])

# vol3: medical(pg1), soccer(pg2)
make_pdf("vol3.pdf", [medical, soccer])

# Statement and Cover Letter
def make_text_pdf(filename, title, content):
    c = canvas.Canvas(os.path.join(out_dir, filename), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, title)
    c.setFont("Helvetica", 12)
    y = 720
    for line in content.split('\n'):
        c.drawString(50, y, line)
        y -= 20
    c.save()

make_text_pdf("Reimbursement_Statement.pdf", "Itemized Reimbursement Statement", 
    "Total Billed: $5,130.70\nTotal Owed (Net): $1,242.25\n\n- Mortgage: $3,500.00 (Owed: $1,750.00)\n- Utilities: $335.70 (Owed: $167.85)\n- Pool: $150.00 (Owed: $75.00)\n- School/Tuition: $1,200.00 (Owed: $144.00)\n- Medical/Dental/Vision: $45.00 (Owed: $5.40)\n- Extracurriculars: $200.00 (Owed: $100.00)")

make_text_pdf("Reimbursement_Cover_Letter.pdf", "Reimbursement Cover Letter", 
    "Dear Jane,\n\nEnclosed is the reimbursement statement for July 2026.\nThe total amount due is $1,242.25 after subtracting the $1,000.00 I paid directly.\n\nPlease review the attached proof packs.\n\nBest,\nJohn Doe")

print("PDFs generated successfully.")
