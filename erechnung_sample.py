from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from drafthorse.models.accounting import ApplicableTradeTax
from drafthorse.models.document import Document
from drafthorse.models.party import TaxRegistration
from drafthorse.models.payment import PaymentMeans, PaymentTerms
from drafthorse.models.tradelines import LineItem

doc = Document()
doc.context.guideline_parameter.id = "urn:cen.eu:en16931:2017"
doc.header.id = "RE-2026-001"
doc.header.type_code = "380"
doc.header.issue_date_time = date.today()

# seller (made-up data)
doc.trade.agreement.seller.name = "Muster Software GmbH"
doc.trade.agreement.seller.address.line_one = "Musterstrasse 1"
doc.trade.agreement.seller.address.postcode = "20095"
doc.trade.agreement.seller.address.city_name = "Hamburg"
doc.trade.agreement.seller.address.country_id = "DE"
doc.trade.agreement.seller.tax_registrations.add(
    TaxRegistration(id=("VA", "DE000000000"))
)

# buyer (made-up data)
doc.trade.agreement.buyer.name = "Kunde GmbH"
doc.trade.agreement.buyer.address.line_one = "Beispielweg 5"
doc.trade.agreement.buyer.address.postcode = "10115"
doc.trade.agreement.buyer.address.city_name = "Berlin"
doc.trade.agreement.buyer.address.country_id = "DE"

doc.trade.settlement.currency_code = "EUR"
doc.trade.settlement.payment_means.add(PaymentMeans(type_code="ZZZ"))

# one invoice line: 2 x 80.00 EUR, 19 % VAT
li = LineItem()
li.document.line_id = "1"
li.product.name = "Beratung"
li.agreement.gross.amount = Decimal("80.00")
li.agreement.gross.basis_quantity = (Decimal("1.0000"), "C62")
li.agreement.net.amount = Decimal("80.00")
li.agreement.net.basis_quantity = (Decimal("1.0000"), "C62")
li.delivery.billed_quantity = (Decimal("2.0000"), "C62")
li.settlement.trade_tax.type_code = "VAT"
li.settlement.trade_tax.category_code = "S"
li.settlement.trade_tax.rate_applicable_percent = Decimal("19.00")
li.settlement.monetary_summation.total_amount = Decimal("160.00")
doc.trade.items.add(li)

# VAT summary
trade_tax = ApplicableTradeTax()
trade_tax.calculated_amount = Decimal("30.40")
trade_tax.basis_amount = Decimal("160.00")
trade_tax.type_code = "VAT"
trade_tax.category_code = "S"
trade_tax.rate_applicable_percent = Decimal("19.00")
doc.trade.settlement.trade_tax.add(trade_tax)

# totals
ms = doc.trade.settlement.monetary_summation
ms.line_total = Decimal("160.00")
ms.charge_total = Decimal("0.00")
ms.allowance_total = Decimal("0.00")
ms.tax_basis_total = Decimal("160.00")
ms.tax_total = (Decimal("30.40"), "EUR")
ms.grand_total = Decimal("190.40")
ms.due_amount = Decimal("190.40")

terms = PaymentTerms()
terms.due = datetime.now(timezone.utc) + timedelta(days=14)
doc.trade.settlement.terms.add(terms)

# create the XML (it is checked against the official schema)
xml = doc.serialize(schema="FACTUR-X_EXTENDED")

with open("beispiel_erechnung.xml", "wb") as f:
    f.write(xml)

print("Created: beispiel_erechnung.xml")

# read it back
doc2 = Document.parse(xml)
print("Rechnungsnummer:", str(doc2.header.id))
print("Verkäufer:", str(doc2.trade.agreement.seller.name))
print("Käufer:", str(doc2.trade.agreement.buyer.name))