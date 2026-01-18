CREATE TABLE IF NOT EXISTS exchange_rates (
    symbol VARCHAR(50),
    rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
