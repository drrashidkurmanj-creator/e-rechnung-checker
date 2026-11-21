from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pypdf import PdfWriter

from erechnung_lib import check_invoice, read_invoice

# a tiny made-up e-invoice (CII syntax), only for the tests
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice
  xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
  xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument>
    <ram:ID>RE-TEST-1</ram:ID>
    <ram:IssueDateTime><udt:DateTimeString format="102">20261001</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty><ram:Name>Muster GmbH</ram:Name></ram:SellerTradeParty>
      <ram:BuyerTradeParty><ram:Name>Kunde GmbH</ram:Name></ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:ApplicableTradeTax>
        <ram:CalculatedAmount>19.00</ram:CalculatedAmount>
        <ram:BasisAmount>100.00</ram:BasisAmount>
        <ram:RateApplicablePercent>19.00</ram:RateApplicablePercent>
      </ram:ApplicableTradeTax>
      <ram:SpecifiedTradePaymentTerms>
        <ram:DueDateDateTime><udt:DateTimeString format="102">20261015</udt:DateTimeString></ram:DueDateDateTime>
      </ram:SpecifiedTradePaymentTerms>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">19.00</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>119.00</ram:GrandTotalAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""


def good_invoice():
    # a small correct invoice, written by hand (made-up data)
    return {
        "number": "RE-1",
        "date": date(2026, 10, 1),
        "seller": "Muster GmbH",
        "buyer": "Kunde GmbH",
        "net": Decimal("100.00"),
        "vat": Decimal("19.00"),
        "gross": Decimal("119.00"),
        "due": date(2026, 10, 15),
        "vat_lines": [
            {"rate": Decimal("19.00"), "basis": Decimal("100.00"), "tax": Decimal("19.00")}
        ],
    }


def test_good_invoice_has_no_problems():
    assert check_invoice(good_invoice(), {}) == []


def test_wrong_total_is_found():
    data = good_invoice()
    data["gross"] = Decimal("120.00")

    problems = check_invoice(data, {})

    assert "Netto + MwSt stimmt nicht mit Brutto überein" in problems


def test_wrong_vat_amount_is_found():
    data = good_invoice()
    data["vat_lines"][0]["tax"] = Decimal("18.00")

    problems = check_invoice(data, {})

    assert "Steuerbeträge stimmen nicht mit MwSt überein" in problems


def test_duplicate_number_is_found():
    counts = {("Muster GmbH", "RE-1"): 2}

    problems = check_invoice(good_invoice(), counts)

    assert "Doppelte Rechnungsnummer" in problems


def test_missing_number_is_found():
    data = good_invoice()
    data["number"] = ""

    problems = check_invoice(data, {})

    assert "Pflichtangabe fehlt" in problems


def test_two_vat_rates_are_correct():
    data = good_invoice()
    data["net"] = Decimal("150.00")
    data["vat"] = Decimal("22.50")
    data["gross"] = Decimal("172.50")
    data["vat_lines"] = [
        {"rate": Decimal("19.00"), "basis": Decimal("100.00"), "tax": Decimal("19.00")},
        {"rate": Decimal("7.00"), "basis": Decimal("50.00"), "tax": Decimal("3.50")},
    ]

    assert check_invoice(data, {}) == []


@pytest.mark.skipif(
    not Path("eingang/RE-2026-101.xml").exists(), reason="sample file is missing"
)
def test_read_sample_invoice():
    data = read_invoice("eingang/RE-2026-101.xml")

    assert data["number"] == "RE-2026-101"
    assert data["seller"] == "Test Reinigung GmbH"
    assert data["gross"] == Decimal("180.30")
    assert data["net"] + data["vat"] == data["gross"]


def test_read_invoice_from_pdf(tmp_path):
    pdf_file = tmp_path / "test.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_attachment(filename="factur-x.xml", data=SAMPLE_XML.encode("utf-8"))
    writer.write(pdf_file)

    data = read_invoice(pdf_file)

    assert data["number"] == "RE-TEST-1"
    assert data["seller"] == "Muster GmbH"
    assert data["date"] == date(2026, 10, 1)
    assert data["gross"] == Decimal("119.00")
    assert check_invoice(data, {}) == []


def test_pdf_without_xml_is_reported(tmp_path):
    pdf_file = tmp_path / "leer.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(pdf_file)

    with pytest.raises(ValueError):
        read_invoice(pdf_file)