# E-Rechnung Checker

A small Python tool that reads German **e-invoices** (XML in the formats used by *XRechnung* and *ZUGFeRD*), checks them for errors and duplicates, and creates an **Excel overview** with a VAT summary.

## Why

German businesses must be able to receive e-invoices (structured XML instead of a plain PDF), and the obligation to send them is being phased in. Many small offices receive such files but have no easy way to read many of them at once. This tool reads a whole folder and shows the result in one table. Please check the current legal rules for your own situation.

## What it does

- Reads all e-invoice XML files in a folder
- Extracts invoice number, date, seller, buyer, net, VAT, gross and due date
- Checks each invoice:
  - Net + VAT = gross
  - VAT lines add up to the totals
  - Mandatory fields are present
  - Duplicate invoice numbers (same seller, same number)
- Creates an Excel file with:
  - one row per invoice (problem rows in red, days until the due date)
  - totals for all invoices and for the invoices without problems
  - a VAT summary per tax rate

## Quick start

1. Install Python 3 and the libraries:

   ```
   pip install -r requirements.txt
   ```

2. Create made-up sample invoices (this creates the folder `eingang`):

   ```
   python erechnung_make_samples.py
   ```

3. Read and check them:

   ```
   python erechnung_batch.py
   ```

4. Open the result: `Eingangsrechnungen.xlsx`

To use your own files, put the XML files in the folder `eingang`.

## Tests

```
pip install pytest
pytest test_erechnung.py -v
```

## Files

| File | Purpose |
|---|---|
| `erechnung_lib.py` | reading an invoice and checking it (tested) |
| `erechnung_batch.py` | reads a folder and writes the Excel overview |
| `erechnung_make_samples.py` | creates made-up sample invoices |
| `erechnung_sample.py` | creates one example e-invoice |
| `test_erechnung.py` | automated tests |
| `Eingangsrechnungen.xlsx` | example output |

## Limits (please read)

- Currently supports XML in the *Cross Industry Invoice* syntax (used by ZUGFeRD / Factur-X and XRechnung-CII). The *UBL* syntax is not supported yet.
- ZUGFeRD **PDF** files are not read directly yet (the XML inside the PDF must be extracted first). This is planned.
- This tool checks arithmetic and basic fields. It is **not** a legal validator and does not replace the official validation tools.
- All sample data is **made up**. This is a demo and not tax advice.

## Tech

Python, lxml, drafthorse (to create sample files), openpyxl, pytest

---

## Auf Deutsch

Ein kleines Python-Programm, das **E-Rechnungen** (XML im Format von XRechnung bzw. ZUGFeRD) aus einem Ordner liest, auf Fehler und doppelte Rechnungsnummern prüft und eine **Excel-Übersicht** mit MwSt-Zusammenfassung erstellt. Geprüft werden unter anderem: Netto + MwSt = Brutto, Summen der Steuerzeilen, Pflichtangaben und doppelte Rechnungsnummern.

**Wichtig:** Das Programm ist ein Demo-Werkzeug. Es ersetzt weder die offizielle Validierung noch eine steuerliche Beratung. Alle Beispieldaten sind frei erfunden. Aktuell wird die XML-Syntax *Cross Industry Invoice* unterstützt, die UBL-Syntax noch nicht. ZUGFeRD-PDFs werden noch nicht direkt gelesen.
