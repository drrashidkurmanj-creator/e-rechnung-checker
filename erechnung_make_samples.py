import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from drafthorse.models.accounting import ApplicableTradeTax
from drafthorse.models.document import Document
from drafthorse.models.party import TaxRegistration
from drafthorse.models.payment import PaymentMeans, PaymentTerms
from drafthorse.models.tradelines import LineItem

random.seed(11)

# made-up sellers: name, street, postcode, city
sellers = [
    ("Muster Software GmbH", "Musterstrasse 1", "20095", "Hamburg"),
    ("Beispiel Druck GmbH", "Druckerweg 7", "50667", "Köln"),
    ("Demo Büroservice GmbH", "Bürogasse 3", "80331", "München"),
    ("Test Reinigung GmbH", "Sauberweg 12", "70173", "Stuttgart"),
]

buyer = ("Kunde GmbH", "Beispielweg 5", "10115", "Berlin")

# made-up articles: name, unit price, VAT rate in percent
articles = [
    ("Beratung", Decimal("80.00"), 19),
    ("Webseite", Decimal("500.00"), 19),
    ("Wartung", Decimal("50.00"), 19),
    ("Fachbuch", Decimal("29.90"), 7),
    ("Zeitschrift", Decimal("9.50"), 7),
]


def money(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def make_invoice(number, seller, issue_date, lines):
    doc = Document()
    doc.context.guideline_parameter.id = "urn:cen.eu:en16931:2017"
    doc.header.id = number
    doc.header.type_code = "380"
    doc.header.issue_date_time = issue_date

    doc.trade.agreement.seller.name = seller[0]
    doc.trade.agreement.seller.address.line_one = seller[1]
    doc.trade.agreement.seller.address.postcode = seller[2]
    doc.trade.agreement.seller.address.city_name = seller[3]
    doc.trade.agreement.seller.address.country_id = "DE"
    doc.trade.agreement.seller.tax_registrations.add(
        TaxRegistration(id=("VA", "DE000000000"))
    )

    doc.trade.agreement.buyer.name = buyer[0]
    doc.trade.agreement.buyer.address.line_one = buyer[1]
    doc.trade.agreement.buyer.address.postcode = buyer[2]
    doc.trade.agreement.buyer.address.city_name = buyer[3]
    doc.trade.agreement.buyer.address.country_id = "DE"

    doc.trade.settlement.currency_code = "EUR"
    doc.trade.settlement.payment_means.add(PaymentMeans(type_code="ZZZ"))

    bases = {}
    line_no = 1

    for name, price, qty, rate in lines:
        net = money(price * qty)

        li = LineItem()
        li.document.line_id = str(line_no)
        li.product.name = name
        li.agreement.gross.amount = price
        li.agreement.gross.basis_quantity = (Decimal("1.0000"), "C62")
        li.agreement.net.amount = price
        li.agreement.net.basis_quantity = (Decimal("1.0000"), "C62")
        li.delivery.billed_quantity = (Decimal(f"{qty}.0000"), "C62")
        li.settlement.trade_tax.type_code = "VAT"
        li.settlement.trade_tax.category_code = "S"
        li.settlement.trade_tax.rate_applicable_percent = Decimal(f"{rate}.00")
        li.settlement.monetary_summation.total_amount = net
        doc.trade.items.add(li)

        bases[rate] = bases.get(rate, Decimal("0")) + net
        line_no = line_no + 1

    net_total = Decimal("0")
    tax_total = Decimal("0")

    for rate in bases:
        basis = bases[rate]
        tax = money(basis * rate / 100)

        trade_tax = ApplicableTradeTax()
        trade_tax.calculated_amount = tax
        trade_tax.basis_amount = basis
        trade_tax.type_code = "VAT"
        trade_tax.category_code = "S"
        trade_tax.rate_applicable_percent = Decimal(f"{rate}.00")
        doc.trade.settlement.trade_tax.add(trade_tax)

        net_total = net_total + basis
        tax_total = tax_total + tax

    grand = net_total + tax_total

    ms = doc.trade.settlement.monetary_summation
    ms.line_total = net_total
    ms.charge_total = Decimal("0.00")
    ms.allowance_total = Decimal("0.00")
    ms.tax_basis_total = net_total
    ms.tax_total = (tax_total, "EUR")
    ms.grand_total = grand
    ms.due_amount = grand

    terms = PaymentTerms()
    terms.due = datetime.combine(issue_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=14)
    doc.trade.settlement.terms.add(terms)

    return doc.serialize(schema="FACTUR-X_EXTENDED")


folder = Path("eingang")
folder.mkdir(exist_ok=True)

today = date.today()

for i in range(1, 9):
    seller = random.choice(sellers)
    issue_date = today - timedelta(days=random.randint(1, 45))

    lines = []
    for j in range(random.randint(1, 3)):
        name, price, rate = random.choice(articles)
        lines.append((name, price, random.randint(1, 5), rate))

    number = f"RE-2026-{100 + i}"
    xml = make_invoice(number, seller, issue_date, lines)

    with open(folder / f"{number}.xml", "wb") as f:
        f.write(xml)

    print("Created:", number, seller[0])