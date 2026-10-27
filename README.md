# Transaction Reconciliation Engine

A small, self-initiated data-quality project demonstrating how to validate ledger-style entries, reconcile debit and credit totals by batch, and generate a JSON report. It uses **synthetic sample data only** and is intended as a learning/portfolio project, not as a production accounting system.

## Problem statement

Batch data can contain duplicate entry IDs, missing identifiers, invalid or negative amounts, entries with both debit and credit amounts, or unbalanced debit/credit totals. This project checks for these issues before a hypothetical downstream posting step.

## What it demonstrates

- Python CSV parsing and `Decimal` arithmetic for financial values
- Row-level validation and batch-level debit/credit reconciliation
- A command-line interface and machine-readable JSON output
- Unit tests using Python's built-in `unittest`
- SQL aggregation for batch-level reconciliation

## Project structure

```text
transaction-reconciliation-engine/
├── data/
│   └── sample_ledger_entries.csv
├── reports/                     # generated report output
├── sql/
│   └── batch_reconciliation.sql
├── src/
│   ├── __init__.py
│   └── reconcile.py
├── tests/
│   └── test_reconcile.py
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 or newer
- No third-party Python packages are required

## Run the validator

From the repository root:

```bash
python -m src.reconcile --input data/sample_ledger_entries.csv --output reports/reconciliation_report.json
```

The sample file intentionally includes both a balanced batch and invalid/unbalanced examples, so the command can return a non-zero exit code. That is expected: the tool is detecting the sample problems. Inspect `reports/reconciliation_report.json` for row-level issues and batch totals.

To run the unit tests:

```bash
python -m unittest discover -s tests -v
```

## Validation rules

1. Required identifiers must be present.
2. Entry IDs must be unique in the input file.
3. Debit and credit amounts must be valid decimal numbers and must not be negative.
4. Each entry must contain a positive amount on exactly one side (debit or credit).
5. Total debits must equal total credits for each batch.

## Example report fields

- `status`: `PASS` only when no row-level or batch-level issues are found
- `row_count` and `batch_count`
- `row_issues`: row number, entry ID when available, and issue description
- `batches`: debit total, credit total, difference, and balance status

## Scope and limitations

This is a portfolio demonstration with a deliberately small synthetic CSV. It does not connect to a bank, ledger, Oracle instance, Azure service, or a production system. It does not authorize or execute financial postings. A production implementation would need agreed accounting rules, lineage, access controls, audit requirements, observability, and domain validation.

## Next improvements

- Add a configurable materiality/tolerance rule if a business case requires it
- Add structured logging and a summary CSV
- Load the sample data into SQLite and compare results with the SQL query
- Add CI to run unit tests on every pull request
