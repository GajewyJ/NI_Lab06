import json
import pytest
from src.manager import Manager
from src.models import Parameters


def test_tenants_total_due_equals_apartment_costs(tmp_path):
    (tmp_path / "apartments.json").write_text(json.dumps({
        "apt_1": {
            "key": "apt_1", "name": "M1", "location": "Poznań", "area_m2": 50.0,
            "rooms": {"r1": {"name": "P1", "area_m2": 15.0}, "r2": {"name": "P2", "area_m2": 15.0}}
        }
    }))
    (tmp_path / "tenants.json").write_text(json.dumps({
        "t1": {"name": "Jan", "apartment": "apt_1", "room": "r1", "rent_pln": 1000, "deposit_pln": 1000, "date_agreement_from": "2026-01-01", "date_agreement_to": "2026-12-31"},
        "t2": {"name": "Anna", "apartment": "apt_1", "room": "r2", "rent_pln": 1000, "deposit_pln": 1000, "date_agreement_from": "2026-01-01", "date_agreement_to": "2026-12-31"},
    }))
    (tmp_path / "bills.json").write_text(json.dumps([
        {"amount_pln": 450.50, "date_due": "2026-05-10", "apartment": "apt_1", "settlement_year": 2026, "settlement_month": 5, "type": "czynsz"},
        {"amount_pln": 149.50, "date_due": "2026-05-15", "apartment": "apt_1", "settlement_year": 2026, "settlement_month": 5, "type": "prąd"},
    ]))
    (tmp_path / "transfers.json").write_text("[]")

    manager = Manager(Parameters(
        apartments_json_path=str(tmp_path / "apartments.json"),
        tenants_json_path=str(tmp_path / "tenants.json"),
        bills_json_path=str(tmp_path / "bills.json"),
        transfers_json_path=str(tmp_path / "transfers.json"),
    ))

    apartment_costs = manager.get_apartment_costs("apt_1", 2026, 5)
    settlement = manager.get_settlement("apt_1", 2026, 5)
    tenants_settlements = manager.create_tenants_settlements(settlement)

    assert sum(ts.total_due_pln for ts in tenants_settlements) == pytest.approx(apartment_costs)


def test_get_tax_calculates_rounded_monthly_tax(tmp_path):
    (tmp_path / "apartments.json").write_text("{}")
    (tmp_path / "tenants.json").write_text("{}")
    (tmp_path / "bills.json").write_text("[]")
    (tmp_path / "transfers.json").write_text(json.dumps([
        # Przelewy za maj 2026: suma = 3500.0 PLN -> 3500 * 0.085 = 297.5 -> round() = 298
        {"amount_pln": 1500.0, "date": "2026-05-05", "settlement_year": 2026, "settlement_month": 5, "tenant": "Jan"},
        {"amount_pln": 2000.0, "date": "2026-05-08", "settlement_year": 2026, "settlement_month": 5, "tenant": "Anna"},
        # Przelew za czerwiec 2026 (powinien zostać zignorowany)
        {"amount_pln": 1800.0, "date": "2026-06-05", "settlement_year": 2026, "settlement_month": 6, "tenant": "Jan"},
    ]))

    manager = Manager(Parameters(
        apartments_json_path=str(tmp_path / "apartments.json"),
        tenants_json_path=str(tmp_path / "tenants.json"),
        bills_json_path=str(tmp_path / "bills.json"),
        transfers_json_path=str(tmp_path / "transfers.json"),
    ))

    assert manager.get_tax(year=2026, month=5, tax_rate=0.085) == 298