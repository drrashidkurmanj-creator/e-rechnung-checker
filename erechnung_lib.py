from datetime import datetime
from decimal import Decimal
from lxml import etree


def get(root, *names):
    # find the first element by its name (ignores the prefix in front of it)
    path = "//" + "/".join(f"*[local-name()='{n}']" for n in names)
    found = root.xpath(path)
    if found and found[0].text:
        return found[0].text.strip()
    return ""


def child_text(element, name):
    found = element.xpath(f"*[local-name()='{name}']")
    if found and found[0].text:
        return found[0].text.strip()
    return ""


def to_date(text):
    if not text:
        return None
    return datetime.strptime(text[:8], "%Y%m%d").date()


def read_invoice(file_name):
    root = etree.parse(str(file_name)).getroot()

    vat_lines = []
    path = (
        "//*[local-name()='ApplicableHeaderTradeSettlement']"
        "/*[local-name()='ApplicableTradeTax']"
    )

    for element in root.xpath(path):
        vat_lines.append(
            {
                "rate": Decimal(child_text(element, "RateApplicablePercent") or "0"),
                "basis": Decimal(child_text(element, "BasisAmount") or "0"),
                "tax": Decimal(child_text(element, "CalculatedAmount") or "0"),
            }
        )

    return {
        "number": get(root, "ExchangedDocument", "ID"),
        "date": to_date(get(root, "ExchangedDocument", "IssueDateTime", "DateTimeString")),
        "seller": get(root, "SellerTradeParty", "Name"),
        "buyer": get(root, "BuyerTradeParty", "Name"),
        "net": Decimal(get(root, "TaxBasisTotalAmount") or "0"),
        "vat": Decimal(get(root, "TaxTotalAmount") or "0"),
        "gross": Decimal(get(root, "GrandTotalAmount") or "0"),
        "due": to_date(
            get(root, "SpecifiedTradePaymentTerms", "DueDateDateTime", "DateTimeString")
        ),
        "vat_lines": vat_lines,
    }

def check_invoice(data, counts):
    problems = []

    if data["net"] + data["vat"] != data["gross"]:
        problems.append("Netto + MwSt stimmt nicht mit Brutto überein")

    basis_sum = sum(v["basis"] for v in data["vat_lines"])
    tax_sum = sum(v["tax"] for v in data["vat_lines"])

    if basis_sum != data["net"]:
        problems.append("Steuerbasis stimmt nicht mit Netto überein")

    if tax_sum != data["vat"]:
        problems.append("Steuerbeträge stimmen nicht mit MwSt überein")

    if not data["number"] or not data["seller"] or data["date"] is None:
        problems.append("Pflichtangabe fehlt")

    if counts.get((data["seller"], data["number"]), 0) > 1:
        problems.append("Doppelte Rechnungsnummer")

    return problems


if __name__ == "__main__":
    data = read_invoice("eingang/RE-2026-101.xml")

    for key in data:
        print(key, ":", data[key])