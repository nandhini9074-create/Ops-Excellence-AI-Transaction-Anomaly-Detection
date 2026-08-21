ALTER TABLE merchant_whitelists ADD COLUMN IF NOT EXISTS dormancy_suppressed_until TIMESTAMP WITH TIME ZONE;
