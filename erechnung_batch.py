from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from erechnung_lib import check_invoice, read_invoice

today = date.today()
folder = Path("eingang")

invoices = []

for file in sorted(folder.glob("*.xml")):
    data = read_invoice(file)
    data["file"] = file.name
    invoices.append(data)

# how often does each pair (seller, invoice number) appear?
counts = Counter((d["seller"], d["number"]) for d in invoices)

red_fill = PatternFill("solid", fgColor="FFC7CE")

wb = Workbook()
ws = wb.active
ws.title = "Rechnungen"

ws.append(
    [
        "Datei",
        "Rechnungsnummer",
        "Datum",
        "Verkäufer",
        "Käufer",
        "Netto",
        "MwSt",
        "Brutto",
        "Fällig am",
        "Tage bis Fälligkeit",
        "Prüfung",
    ]
)

ok_invoices = []
problem_count = 0

for data in invoices:
    problems = check_invoice(data, counts)

    if problems:
        problem_count = problem_count + 1
        status = "; ".join(problems)
    else:
        ok_invoices.append(data)
        status = "OK"

    if data["due"]:
        days = (data["due"] - today).days
    else:
        days = ""

    ws.append(
        [
            data["file"],
            data["number"],
            data["date"],
            data["seller"],
            data["buyer"],
            float(data["net"]),
            float(data["vat"]),
            float(data["gross"]),
            data["due"],
            days,
            status,
        ]
    )

    if problems:
        for cell in ws[ws.max_row]:
            cell.fill = red_fill

last = ws.max_row

ws.append(
    [
        "Gesamt (alle)",
        "",
        "",
        "",
        "",
        f"=SUM(F2:F{last})",
        f"=SUM(G2:G{last})",
        f"=SUM(H2:H{last})",
    ]
)
ws.append(
    [
        "Gesamt (nur Prüfung OK)",
        "",
        "",
        "",
        "",
        f'=SUMIF(K2:K{last},"OK",F2:F{last})',
        f'=SUMIF(K2:K{last},"OK",G2:G{last})',
        f'=SUMIF(K2:K{last},"OK",H2:H{last})',
    ]
)

for cell in ws[1]:
    cell.font = Font(bold=True)

for r in (ws.max_row - 1, ws.max_row):
    for cell in ws[r]:
        cell.font = Font(bold=True)

for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
    for cell in row:
        cell.number_format = "DD.MM.YYYY"

for row in ws.iter_rows(min_row=2, min_col=9, max_col=9):
    for cell in row:
        cell.number_format = "DD.MM.YYYY"

for row in ws.iter_rows(min_row=2, min_col=6, max_col=8):
    for cell in row:
        cell.number_format = "0.00"

widths = {"A": 26, "B": 18, "C": 12, "D": 26, "E": 16, "F": 12, "G": 12, "H": 12, "I": 12, "J": 20, "K": 60}
for letter in widths:
    ws.column_dimensions[letter].width = widths[letter]

# second sheet: VAT per rate (only invoices without problems)
by_rate = {}

for data in ok_invoices:
    for v in data["vat_lines"]:
        rate = v["rate"]

        if rate not in by_rate:
            by_rate[rate] = {"basis": Decimal("0"), "tax": Decimal("0")}

        by_rate[rate]["basis"] = by_rate[rate]["basis"] + v["basis"]
        by_rate[rate]["tax"] = by_rate[rate]["tax"] + v["tax"]

vs = wb.create_sheet("MwSt")
vs.append(["Steuersatz (%)", "Steuerbasis (EUR)", "Steuerbetrag (EUR)"])

for rate in sorted(by_rate):
    vs.append([float(rate), float(by_rate[rate]["basis"]), float(by_rate[rate]["tax"])])

last = vs.max_row
vs.append(["Gesamt", f"=SUM(B2:B{last})", f"=SUM(C2:C{last})"])
vs.append([])
vs.append(["Nur Rechnungen mit Prüfung OK"])

for cell in vs[1]:
    cell.font = Font(bold=True)

for cell in vs[last + 1]:
    cell.font = Font(bold=True)

for row in vs.iter_rows(min_row=2, min_col=2, max_col=3):
    for cell in row:
        cell.number_format = "0.00"

vs.column_dimensions["A"].width = 30
vs.column_dimensions["B"].width = 20
vs.column_dimensions["C"].width = 20

wb.save("Eingangsrechnungen.xlsx")

total_gross = sum(d["gross"] for d in invoices)
total_ok = sum(d["gross"] for d in ok_invoices)

print("Rechnungen gelesen:", len(invoices))
print("Mit Problemen:", problem_count)
print(f"Brutto gesamt (alle): {total_gross:.2f} EUR")
print(f"Brutto gesamt (nur OK): {total_ok:.2f} EUR")
print("Created: Eingangsrechnungen.xlsx")