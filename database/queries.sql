-- Example queries for project demonstration (run connected to blood_bank_db).
SELECT blood_group_code, available_quantity_ml FROM blood_stock ORDER BY blood_group_code;
SELECT screening_status, COUNT(*) FROM donation GROUP BY screening_status ORDER BY screening_status;
SELECT d.donor_id, d.full_name, COUNT(do.donation_id) AS donation_count
FROM donor d LEFT JOIN donation do ON do.donor_id=d.donor_id
GROUP BY d.donor_id, d.full_name ORDER BY donation_count DESC;
SELECT br.request_id, h.hospital_name, br.blood_group_code,
       br.quantity_requested_ml,
       COALESCE(SUM(bi.quantity_issued_ml),0) AS issued_ml,
       br.request_status
FROM blood_request br JOIN hospital h ON h.hospital_id=br.hospital_id
LEFT JOIN blood_issue bi ON bi.request_id=br.request_id
GROUP BY br.request_id,h.hospital_name ORDER BY br.request_date DESC;
