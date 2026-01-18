CREATE TABLE IF NOT EXISTS trained_models_stats (
    s3_key VARCHAR(200),
    model_name VARCHAR(200),
    mae FLOAT,
    training_set_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
