-- Run while connected to blood_bank_db. Safe to run repeatedly on a new/current schema.
CREATE TABLE IF NOT EXISTS blood_group (
    blood_group_code VARCHAR(3) PRIMARY KEY,
    description VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('ADMIN', 'STAFF')),
    phone VARCHAR(15) UNIQUE,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS donor (
    donor_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    blood_group_code VARCHAR(3) NOT NULL REFERENCES blood_group(blood_group_code),
    phone VARCHAR(15) UNIQUE,
    email VARCHAR(100) UNIQUE,
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

ALTER TABLE donor ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS donation (
    donation_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    donor_id INTEGER NOT NULL REFERENCES donor(donor_id),
    donation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    blood_group_code VARCHAR(3) NOT NULL REFERENCES blood_group(blood_group_code),
    quantity_ml INTEGER NOT NULL CHECK (quantity_ml > 0),
    screening_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
      CHECK (screening_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    staff_id INTEGER NOT NULL REFERENCES staff(staff_id)
);

CREATE TABLE IF NOT EXISTS blood_stock (
    stock_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    blood_group_code VARCHAR(3) NOT NULL UNIQUE REFERENCES blood_group(blood_group_code),
    available_quantity_ml INTEGER NOT NULL DEFAULT 0 CHECK (available_quantity_ml >= 0),
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hospital (
    hospital_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hospital_name VARCHAR(150) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(100),
    address TEXT
);

CREATE TABLE IF NOT EXISTS blood_request (
    request_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hospital_id INTEGER NOT NULL REFERENCES hospital(hospital_id),
    blood_group_code VARCHAR(3) NOT NULL REFERENCES blood_group(blood_group_code),
    quantity_requested_ml INTEGER NOT NULL CHECK (quantity_requested_ml > 0),
    request_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    request_status VARCHAR(25) NOT NULL DEFAULT 'PENDING'
      CHECK (request_status IN ('PENDING', 'APPROVED', 'PARTIALLY_FULFILLED', 'FULFILLED', 'REJECTED')),
    staff_id INTEGER REFERENCES staff(staff_id)
);

CREATE TABLE IF NOT EXISTS blood_issue (
    issue_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES blood_request(request_id),
    issue_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantity_issued_ml INTEGER NOT NULL CHECK (quantity_issued_ml > 0),
    staff_id INTEGER NOT NULL REFERENCES staff(staff_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    staff_id INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(100),
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_donation_group_status ON donation(blood_group_code, screening_status);
CREATE INDEX IF NOT EXISTS idx_request_status_date ON blood_request(request_status, request_date DESC);
CREATE INDEX IF NOT EXISTS idx_issue_request ON blood_issue(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at DESC);

INSERT INTO blood_group (blood_group_code, description) VALUES
 ('A+','A Positive'), ('A-','A Negative'), ('B+','B Positive'), ('B-','B Negative'),
 ('AB+','AB Positive'), ('AB-','AB Negative'), ('O+','O Positive'), ('O-','O Negative')
ON CONFLICT (blood_group_code) DO NOTHING;

INSERT INTO blood_stock (blood_group_code)
SELECT blood_group_code FROM blood_group
ON CONFLICT (blood_group_code) DO NOTHING;
