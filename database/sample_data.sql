-- Optional starter data. Run AFTER schema.sql and AFTER creating staff with setup_admin.py.
-- The staff_id value below assumes the first account has staff_id=1; adjust if needed.
INSERT INTO hospital (hospital_name, phone, email, address) VALUES
 ('City General Hospital', '9200000001', 'city@example.com', 'Main Road'),
 ('Green Life Hospital', '9200000002', 'green@example.com', 'Central Avenue');

INSERT INTO donor (full_name, date_of_birth, gender, blood_group_code, phone, email, address) VALUES
 ('Ravi Kumar', '1998-05-12', 'Male', 'O+', '9100000001', 'ravi@example.com', 'City Centre'),
 ('Anitha Devi', '2000-08-21', 'Female', 'A+', '9100000002', 'anitha@example.com', 'North Street');

-- Demo donations start as PENDING; approve them in Donation Management to increase stock.
INSERT INTO donation (donor_id, donation_date, blood_group_code, quantity_ml, screening_status, staff_id) VALUES
 (1, CURRENT_DATE, 'O+', 350, 'PENDING', 1),
 (2, CURRENT_DATE, 'A+', 350, 'PENDING', 1);

INSERT INTO blood_request (hospital_id, blood_group_code, quantity_requested_ml, request_status, staff_id) VALUES
 (1, 'O+', 250, 'PENDING', 1),
 (2, 'A+', 200, 'PENDING', 1);
