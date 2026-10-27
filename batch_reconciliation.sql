-- SQL example for batch-level debit/credit reconciliation.
-- Syntax is compatible with SQLite; adapt data types and date handling for other databases.

CREATE TABLE IF NOT EXISTS ledger_entries (
    batch_date     TEXT NOT NULL,
    batch_id       TEXT NOT NULL,
    entry_id       TEXT NOT NULL,
    account_id     TEXT NOT NULL,
    reference_id   TEXT NOT NULL,
    debit_amount   NUMERIC NOT NULL,
    credit_amount  NUMERIC NOT NULL
);

SELECT
    batch_date,
    batch_id,
    ROUND(SUM(debit_amount), 2) AS debit_total,
    ROUND(SUM(credit_amount), 2) AS credit_total,
    ROUND(SUM(debit_amount) - SUM(credit_amount), 2) AS difference,
    CASE
        WHEN ROUND(SUM(debit_amount) - SUM(credit_amount), 2) = 0 THEN 'BALANCED'
        ELSE 'UNBALANCED'
    END AS reconciliation_status
FROM ledger_entries
GROUP BY batch_date, batch_id
ORDER BY batch_date, batch_id;
