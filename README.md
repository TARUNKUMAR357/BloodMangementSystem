<<<<<<< HEAD
# LIFEPOINT — Blood Bank Management System

A Python desktop DBMS project using Tkinter/CustomTkinter, PostgreSQL and psycopg 3. It includes staff login, a premium dashboard with a light/dark switch, donor and donation management, stock, hospitals, requests, blood issues, and CSV reports.

## Project structure

```text
BloodBankManagement/
├── app.py
├── auth.py
├── login_ui.py
├── dashboard.py
├── permissions.py
├── validators.py
├── set_staff_password.py
├── test_connection.py
├── config/
│   └── database.py
├── database/
│   ├── schema.sql
│   ├── sample_data.sql
│   └── queries.sql
├── services/                 # service-layer extension points
├── donor_ui.py
├── donation_ui.py
├── stock_ui.py
├── hospital_ui.py
├── blood_request_ui.py
├── blood_issue_ui.py
└── reports_ui.py
```

## 1. Requirements

- Python 3.10 or newer
- PostgreSQL 14 or newer recommended
- `pip`

## 2. Create the database

Open pgAdmin or a terminal. Create the database once:

```sql
CREATE DATABASE blood_bank_db;
```

Then connect to `blood_bank_db` and run `database/schema.sql`.

Using `psql`:

```bash
psql -U postgres -d blood_bank_db -f database/schema.sql
```

The schema creates the tables and seeds the eight blood groups and their empty stock rows. The optional sample data assumes the first staff row has `staff_id = 1`; create the administrator first before running it, or adjust the staff IDs in that file to match your database. Run it with `psql -U postgres -d blood_bank_db -f database/sample_data.sql`.

## 3. Install Python dependencies

From the project root:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then install packages:

```bash
python -m pip install -r requirements.txt
```

## 4. Configure PostgreSQL connection

The application reads database settings from environment variables. Set these in the same terminal where you run the app.

Windows PowerShell:

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="blood_bank_db"
$env:DB_USER="postgres"
$env:DB_PASSWORD="YOUR_POSTGRES_PASSWORD"
```

macOS/Linux:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=blood_bank_db
export DB_USER=postgres
export DB_PASSWORD='YOUR_POSTGRES_PASSWORD'
```

Do not store real database passwords in source files or commit them to version control. `.env.example` is a reference template; this project does not automatically load `.env` files.

## 5. Create a staff account and set its password

The schema intentionally does not include a default account/password. Create an initial administrator row with a temporary placeholder hash, then use `set_staff_password.py` to set a real PBKDF2 password.

First, in pgAdmin or `psql` connected to `blood_bank_db`, run:

```sql
INSERT INTO staff (full_name, role, username, password_hash)
VALUES ('System Administrator', 'ADMIN', 'admin', 'temporary-placeholder');
```

Then run:

```bash
python set_staff_password.py
```

Enter `admin` as the username and choose a password of at least 12 characters. The script replaces the placeholder with a PBKDF2-SHA256 hash. Do not use the placeholder account until the password is set.

## 6. Test the connection and launch

```bash
python test_connection.py
python app.py
```

Sign in using the username and password set in step 5.

## 7. Suggested demo workflow

1. Add a donor.
2. Record a donation; it starts as `PENDING`.
3. Select a pending donation and approve or reject it. Approval adds its quantity to stock.
4. Add a hospital and create a blood request.
5. Approve the request.
6. Issue blood against the approved request. The app checks the remaining request quantity and stock, then records the issue and decreases stock in the same transaction.
7. Open Reports & Analytics and export a CSV report.

## UI note

The login and dashboard use CustomTkinter for the premium style and theme switch. The seven existing management modules are preserved from the supplied project and still use standard Tkinter/ttk controls; their database workflows are retained, but they may not fully follow the dashboard theme yet.

## Important notes

- This is an academic project and should be tested against your own PostgreSQL installation before demonstration.
- The inventory model stores aggregate millilitres by blood group; it does not track individual bags, component types, expiry, cross-matching, or clinical traceability. It is not suitable for real clinical use.
- UI role restrictions are not a substitute for PostgreSQL permissions. Use a least-privilege database role for deployment.
- `database/sample_data.sql` is optional. If IDs in your database differ, update the sample foreign-key values before running it.
=======
# BloodMangementSystem
>>>>>>> 9afa154d7ed240fdad6138418a4d769f7a93b0d5
