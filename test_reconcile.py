import unittest

from src.reconcile import validate_entries


def make_row(entry_id, batch_id="B1", debit="10.00", credit="0.00"):
    return {
        "batch_date": "2026-10-01",
        "batch_id": batch_id,
        "entry_id": entry_id,
        "account_id": f"ACC-{entry_id}",
        "reference_id": f"REF-{batch_id}",
        "debit_amount": debit,
        "credit_amount": credit,
    }


class ValidateEntriesTests(unittest.TestCase):
    def test_balanced_batch_passes(self):
        report = validate_entries([
            make_row("E1", debit="10.00", credit="0.00"),
            make_row("E2", debit="0.00", credit="10.00"),
        ])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["batches"][0]["difference"], "0.00")

    def test_unbalanced_batch_fails(self):
        report = validate_entries([
            make_row("E1", debit="10.00", credit="0.00"),
            make_row("E2", debit="0.00", credit="8.00"),
        ])
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["batches"][0]["balanced"])

    def test_duplicate_entry_id_is_reported(self):
        report = validate_entries([
            make_row("E1", debit="10.00", credit="0.00"),
            make_row("E1", debit="0.00", credit="10.00"),
        ])
        self.assertTrue(any("duplicate entry_id" in issue["issue"] for issue in report["row_issues"]))

    def test_negative_amount_is_reported(self):
        report = validate_entries([make_row("E1", debit="-10.00", credit="0.00")])
        self.assertTrue(any("must not be negative" in issue["issue"] for issue in report["row_issues"]))

    def test_both_sides_positive_is_reported(self):
        report = validate_entries([make_row("E1", debit="10.00", credit="10.00")])
        self.assertTrue(any("both debit and credit" in issue["issue"] for issue in report["row_issues"]))


if __name__ == "__main__":
    unittest.main()
