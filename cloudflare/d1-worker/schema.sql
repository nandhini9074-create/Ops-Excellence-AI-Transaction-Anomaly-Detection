-- Drop table if exists
DROP TABLE IF EXISTS historical_transactions;

-- Create historical transactions table
CREATE TABLE historical_transactions (
    id TEXT PRIMARY KEY,
    transaction_id TEXT,
    transaction_no TEXT,
    group_id TEXT,
    group_transaction_id TEXT,
    payout_transaction_id TEXT,
    outlet_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    transaction_timestamp TEXT NOT NULL,
    posting_timestamp TEXT,
    txn_date TEXT NOT NULL,
    txn_hour TEXT NOT NULL,
    created_on TEXT,
    last_updated_on TEXT,
    silver_updated_at TEXT,
    transaction_amount REAL NOT NULL,
    card_scheme TEXT,
    merchant_name TEXT,
    outlet_name TEXT,
    outlet_status TEXT,
    archived_at TEXT NOT NULL
);

CREATE INDEX idx_hist_txn_date ON historical_transactions(txn_date);
CREATE INDEX idx_hist_timestamp ON historical_transactions(transaction_timestamp);
CREATE INDEX idx_hist_merchant_id ON historical_transactions(merchant_id);
CREATE INDEX idx_hist_outlet_id ON historical_transactions(outlet_id);
CREATE INDEX idx_hist_group_id ON historical_transactions(group_id);
CREATE INDEX idx_hist_group_txn_id ON historical_transactions(group_transaction_id);
