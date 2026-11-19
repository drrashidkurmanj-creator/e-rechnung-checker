from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from erechnung_lib import check_invoice, read_invoice


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