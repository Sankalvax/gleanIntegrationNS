CREATE DATABASE IF NOT EXISTS glean_netsuite_sync;

USE glean_netsuite_sync;

CREATE TABLE IF NOT EXISTS auth_credentials (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    glean_account VARCHAR(100) NOT NULL,
    glean_api_token TEXT NOT NULL,
    netsuite_account_id VARCHAR(100) NOT NULL,
    netsuite_consumer_key TEXT NOT NULL,
    netsuite_consumer_secret TEXT NOT NULL,
    netsuite_token TEXT NOT NULL,
    netsuite_token_secret TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);