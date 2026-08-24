CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS merchants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    mcc VARCHAR(4),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outlets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location_city VARCHAR(100),
    location_country VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
    risk_score FLOAT DEFAULT 0.0,
    segment VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(100),
    transaction_no VARCHAR(100),
    group_id VARCHAR(100),
    group_transaction_id VARCHAR(100),
    payout_transaction_id VARCHAR(100),
    outlet_id UUID NOT NULL REFERENCES outlets(id),
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    profile_id UUID REFERENCES profiles(id),
    transaction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    posting_timestamp TIMESTAMP WITH TIME ZONE,
    txn_date DATE NOT NULL,
    txn_hour INTEGER NOT NULL,
    created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    silver_updated_at TIMESTAMP WITH TIME ZONE,
    transaction_amount DECIMAL(15,2) NOT NULL,
    card_scheme VARCHAR(50),
    merchant_name VARCHAR(255),
    outlet_name VARCHAR(255),
    outlet_status VARCHAR(50),
    
    CONSTRAINT exclusive_transaction_type CHECK (
        (
            transaction_id IS NOT NULL 
            AND transaction_no IS NOT NULL 
            AND group_id IS NULL 
            AND group_transaction_id IS NULL
        ) 
        OR 
        (
            transaction_id IS NULL 
            AND transaction_no IS NULL 
            AND group_id = '1b6c6a30-27f7-11ef-b9a3-d70b94feac5e' 
            AND group_transaction_id IS NOT NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(transaction_timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_outlet ON transactions(outlet_id);

CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_id VARCHAR(100) NOT NULL,
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    merchant_name VARCHAR(255) NOT NULL,
    outlet_id UUID NOT NULL REFERENCES outlets(id),
    outlet_name VARCHAR(255) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    anomaly_score FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN',
    assigned_to VARCHAR(100),
    root_cause TEXT,
    resolution TEXT,
    user_typing TEXT,
    scheme VARCHAR(50),
    remarks TEXT,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL,
    root_cause TEXT,
    comments TEXT,
    user_typing TEXT,
    submitted_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS baselines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL,
    analyzed_days INTEGER NOT NULL,
    data_points_count INTEGER NOT NULL,
    is_active VARCHAR(10) DEFAULT 'true',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processing_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    anomalies_detected INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS merchant_whitelists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    outlet_id UUID REFERENCES outlets(id) ON DELETE CASCADE,
    false_positive_count INTEGER DEFAULT 0,
    threshold_multiplier FLOAT DEFAULT 1.0,
    is_whitelisted VARCHAR(10) DEFAULT 'false',
    dormancy_suppressed_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

