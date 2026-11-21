from fpdf import FPDF
from pypdf import PdfWriter

# 1) a normal visible PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=16)
pdf.cell(0, 10, "Rechnung RE-2026-001 (Beispiel)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", size=11)
pdf.cell(0, 8, "Muster Software GmbH an Kunde GmbH", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Brutto: 190,40 EUR", new_x="LMARGIN", new_y="NEXT")
pdf.output("beispiel_sichtbar.pdf")

# 2) the e-invoice XML we created earlier
with open("beispiel_erechnung.xml", "rb") as f:
    xml = f.read()

# 3) put the XML into the PDF as an attachment
writer = PdfWriter(clone_from="beispiel_sichtbar.pdf")
writer.add_attachment(filename="factur-x.xml", data=xml)
writer.write("beispiel_zugferd.pdf")

print("Created: beispiel_zugferd.pdf")