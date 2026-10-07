CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS infrastructure;
CREATE TABLE IF NOT EXISTS infrastructure.persistence_probe (
    id text PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now()
);
