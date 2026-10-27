"""Validate synthetic ledger entries and reconcile debit/credit totals by batch."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = (
    "batch_date",
    "batch_id",
    "entry_id",
    "account_id",
    "reference_id",
    "debit_amount",
    "credit_amount",
)


def _to_decimal(value: str, *, row_number: int, field: str, issues: list[dict[str, Any]]) -> Decimal | None:
    """Parse a decimal amount; record a row issue instead of raising on bad data."""
    try:
        amount = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        issues.append({"row_number": row_number, "entry_id": None, "issue": f"{field} is not a valid decimal"})
        return None
    if not amount.is_finite():
        issues.append({"row_number": row_number, "entry_id": None, "issue": f"{field} must be finite"})
        return None
    return amount


def validate_entries(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Return row-level validation issues and batch-level debit/credit totals."""
    row_issues: list[dict[str, Any]] = []
    batch_totals: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"debit": Decimal("0"), "credit": Decimal("0")})
    seen_entry_ids: set[str] = set()
    row_count = 0

    for row_number, row in enumerate(rows, start=2):  # CSV header is line 1
        row_count += 1
        entry_id = (row.get("entry_id") or "").strip()
        batch_id = (row.get("batch_id") or "").strip()
        account_id = (row.get("account_id") or "").strip()
        reference_id = (row.get("reference_id") or "").strip()
        batch_date = (row.get("batch_date") or "").strip()

        for field_name, value in (
            ("batch_date", batch_date),
            ("batch_id", batch_id),
            ("entry_id", entry_id),
            ("account_id", account_id),
            ("reference_id", reference_id),
        ):
            if not value:
                row_issues.append({"row_number": row_number, "entry_id": entry_id or None, "issue": f"{field_name} is required"})

        if entry_id:
            if entry_id in seen_entry_ids:
                row_issues.append({"row_number": row_number, "entry_id": entry_id, "issue": "duplicate entry_id"})
            else:
                seen_entry_ids.add(entry_id)

        debit = _to_decimal(row.get("debit_amount", ""), row_number=row_number, field="debit_amount", issues=row_issues)
        credit = _to_decimal(row.get("credit_amount", ""), row_number=row_number, field="credit_amount", issues=row_issues)

        if debit is not None and debit < 0:
            row_issues.append({"row_number": row_number, "entry_id": entry_id or None, "issue": "debit_amount must not be negative"})
        if credit is not None and credit < 0:
            row_issues.append({"row_number": row_number, "entry_id": entry_id or None, "issue": "credit_amount must not be negative"})

        if debit is not None and credit is not None:
            if debit > 0 and credit > 0:
                row_issues.append({"row_number": row_number, "entry_id": entry_id or None, "issue": "an entry cannot have both debit and credit amounts greater than zero"})
            elif debit == 0 and credit == 0:
                row_issues.append({"row_number": row_number, "entry_id": entry_id or None, "issue": "either debit or credit must be greater than zero"})

            # Include parseable amounts in the totals so the report can explain the raw imbalance.
            if batch_id:
                batch_totals[batch_id]["debit"] += debit
                batch_totals[batch_id]["credit"] += credit

    batches: list[dict[str, Any]] = []
    for batch_id in sorted(batch_totals):
        debit_total = batch_totals[batch_id]["debit"]
        credit_total = batch_totals[batch_id]["credit"]
        difference = debit_total - credit_total
        batches.append(
            {
                "batch_id": batch_id,
                "debit_total": str(debit_total.quantize(Decimal("0.01"))),
                "credit_total": str(credit_total.quantize(Decimal("0.01"))),
                "difference": str(difference.quantize(Decimal("0.01"))),
                "balanced": difference == 0,
            }
        )

    unbalanced = [batch for batch in batches if not batch["balanced"]]
    status = "PASS" if not row_issues and not unbalanced else "FAIL"
    return {
        "status": status,
        "row_count": row_count,
        "batch_count": len(batches),
        "row_issues": row_issues,
        "batches": batches,
    }


def load_csv(path: Path) -> list[dict[str, str]]:
    """Load input CSV and validate its header."""
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = set(reader.fieldnames or [])
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            raise ValueError("Input CSV is missing required column(s): " + ", ".join(missing))
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ledger entries and reconcile totals by batch.")
    parser.add_argument("--input", type=Path, required=True, help="Path to the input ledger CSV")
    parser.add_argument("--output", type=Path, required=True, help="Path for the JSON report")
    args = parser.parse_args()

    try:
        rows = load_csv(args.input)
        report = validate_entries(rows)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
