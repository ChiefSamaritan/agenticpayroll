Db URL : 
pip install fastapi uvicorn - make sure it is installed

uvicorn payroll_service:app --reload is the python loader service for the endapi end point running on http://127.0.0.1:8000 

/docs will give you the swagger end point

 pip install sqlalchemy -- for SQLalchemy import 
 pip install prometheus-fastapi-instrumentator - for prometheus monitoring
 pip install weasyprint
 pip install python-dotenv
 pip install psycopg2-binary --> for postgress connection

 pip install -r requirements.txt
terms:
Perfect! Here’s a concise and professional Payroll Glossary Table — great for internal documentation, onboarding, or inclusion in your product help docs.


⸻

# 📘 Payroll Glossary for Global Payroll Systems

| Term                     | Definition                                                                                          | Example / Notes |
|--------------------------|-----------------------------------------------------------------------------------------------------|-----------------|
| **Gross Salary**         | The agreed **annual or monthly base compensation** in the employment contract.                      | ₹950,000/year or $72,000/year |
| **Gross Pay**            | The **total actual earnings** for a specific payroll period. Includes base pay, overtime, bonuses, allowances. | ₹144,300 this month |
| **Base Pay**             | Pay based on standard hours worked (hourly rate × hours worked).                                    | ₹500/hour × 160 hrs = ₹80,000 |
| **Overtime Pay**         | Additional pay for hours worked beyond standard schedule. Often calculated at a premium (e.g., 1.25x). | ₹500/hour × 1.25 × 20 hrs = ₹12,500 |
| **Bonuses**              | Lump-sum performance or discretionary payments included in the pay period.                          | ₹50,000 bonus added |
| **Allowances**           | Extra taxable or non-taxable components (e.g., transport, housing) that may vary by country.         | ₹1,800 transport allowance |
| **Income Tax**           | Tax levied on employee’s earnings. May follow progressive tax brackets.                             | Bracket-based; e.g. ₹20,000 |
| **Social Security**      | Statutory deduction for retirement, pension, or unemployment. May have both employer and employee parts. | 12% for employee, 12.75% employer (India PF) |
| **Health Insurance**     | Mandatory or optional deduction for public or private health coverage.                              | 4% in Philippines |
| **Solidarity Fund**      | Country-specific social contribution (e.g., Colombia).                                               | 1% of gross pay |
| **Total Deductions**     | Sum of all deductions (tax, social security, insurance, other contributions).                        | ₹30,000 deducted |
| **Net Pay**              | Final amount paid to employee after all deductions.                                                  | Gross Pay − Deductions = ₹114,300 |
| **Employer Contributions** | Employer’s statutory costs above the employee’s gross pay (e.g., taxes, benefits, levies).           | e.g., ₹18,000 total employer cost |
| **Payslip**              | Document issued to employee showing detailed breakdown of pay and deductions for a pay cycle.        | PDF format with net, gross, taxes |
| **Payroll Cut-off**      | The day payroll inputs are frozen for calculation (e.g., 15th or 25th).                             | Used for monthly/bi-weekly processing |
| **Pay Frequency**        | How often employees are paid (e.g., monthly, bi-weekly, semi-monthly).                              | Monthly in India, Bi-weekly in US |


Run doucmentation for this Prototype

Data Structures
-- TENANT/COMPANY TABLE (OPTIONAL, for multi-tenant)
CREATE TABLE tenant (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT
);

-- PAYRUN TABLE
CREATE TABLE payrun (
    id                SERIAL        PRIMARY KEY,
    tenant_id         INT           REFERENCES tenant(id),
    period_start      DATE          NOT NULL,
    period_end        DATE          NOT NULL,
    run_date          TIMESTAMPTZ   NOT NULL DEFAULT now(),
    status            VARCHAR(20)   NOT NULL,     -- e.g. 'draft','approved','posted'
    description       TEXT,
    total_gross       NUMERIC(12,2),
    total_net         NUMERIC(12,2),
    total_tax         NUMERIC(12,2),
    total_employer_cost NUMERIC(12,2)
);

-- EMPLOYEE MASTER TABLE
CREATE TABLE employee (
    id              VARCHAR(50)  PRIMARY KEY,
    tenant_id       INT          REFERENCES tenant(id),
    full_name       TEXT         NOT NULL,
    email           TEXT,
    job_title       TEXT,
    department      TEXT,
    country         VARCHAR(50)  NOT NULL,
    tax_id          VARCHAR(50),
    bank_account_last4 VARCHAR(10),
    hire_date       DATE,
    termination_date DATE,
    status          VARCHAR(20) DEFAULT 'active',
    date_of_birth   DATE
);

-- EMPLOYEE PAYSLIP TABLE
CREATE TABLE employee_pay (
    id SERIAL PRIMARY KEY,
    payrun_id   INT  NOT NULL REFERENCES payrun(id) ON DELETE CASCADE,
    employee_id VARCHAR(50) NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    country     VARCHAR(100),
    pay_period  VARCHAR(50),
    pay_type    VARCHAR(20), -- e.g., Monthly, Bi-weekly
    base_pay    NUMERIC(12, 2),
    overtime_pay NUMERIC(12, 2),
    bonuses     NUMERIC(12, 2),
    hours_worked NUMERIC(8, 2),
    overtime_hours NUMERIC(8, 2),
    gross_pay   NUMERIC(12, 2),
    taxable_income NUMERIC(12, 2),
    income_tax  NUMERIC(12, 2),
    social_security NUMERIC(12, 2),
    health_insurance NUMERIC(12, 2),
    solidarity_fund NUMERIC(12, 2),
    total_deductions NUMERIC(12, 2),
    net_pay     NUMERIC(12, 2),
    total_employer_cost NUMERIC(12, 2),
    total_pre_tax NUMERIC(12, 2),
    total_post_tax NUMERIC(12, 2),
    tax_bracket_details JSONB,
    tax_exemptions_applied JSONB,
    country_specific_benefits JSONB,
    issued_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EMPLOYEE ALLOWANCES (one per allowance type per payslip)
CREATE TABLE employee_allowances (
    id SERIAL PRIMARY KEY,
    payslip_id INT NOT NULL REFERENCES employee_pay(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    amount NUMERIC(12, 2),
    pre_tax BOOLEAN DEFAULT FALSE,
    tax_exempt BOOLEAN DEFAULT FALSE
);

-- EMPLOYER CONTRIBUTIONS (one per contribution type per payslip)
CREATE TABLE employer_contributions (
    id SERIAL PRIMARY KEY,
    payslip_id INT NOT NULL REFERENCES employee_pay(id) ON DELETE CASCADE,
    contribution_type VARCHAR(100) NOT NULL,
    amount NUMERIC(12, 2)
);

-- BENEFITS/DEDUCTIONS (pre-tax and post-tax, per payslip)
CREATE TABLE employee_benefits_deductions (
    id SERIAL PRIMARY KEY,
    payslip_id INT NOT NULL REFERENCES employee_pay(id) ON DELETE CASCADE,
    deduction_type VARCHAR(100),       -- pre_tax / post_tax
    benefit_name VARCHAR(100),
    amount NUMERIC(12, 2),
    payer VARCHAR(20)                  -- 'employee' or 'employer'
);

-- INDEXES FOR PERFORMANCE 
CREATE INDEX idx_employee_pay_employee ON employee_pay(employee_id);
CREATE INDEX idx_employee_pay_payrun ON employee_pay(payrun_id);

CREATE INDEX idx_employee_allowances_payslip ON employee_allowances(payslip_id);
CREATE INDEX idx_employer_contributions_payslip ON employer_contributions(payslip_id);
CREATE INDEX idx_employee_benefits_deductions_payslip ON employee_benefits_deductions(payslip_id);

AgenticPayroll/
│
├── app/
│   ├── __init__.py
│   ├── main.py                # Entry point (was your payroll_service.py)
│   ├── models/                 # Pydantic models (request/response + ORM models)
│   │   ├── __init__.py
│   │   ├── employee.py         # Employee, Allowances, BenefitsOptIn, CompanyMetadata
│   │   ├── payroll_record.py   # PayrollRecord SQLAlchemy model
│   │   ├── country_config.py   # Functions for loading config
│
│   ├── services/               # Business logic and calculators
│   │   ├── __init__.py
│   │   ├── gross_pay.py         # calculate_gross_pay()
│   │   ├── deductions.py        # calculate_deductions()
│   │   ├── employer_costs.py    # calculate_employer_costs()
│   │   ├── benefits.py          # calculate_benefits()
│   │   ├── payslip.py           # generate_payslip()
│
│   ├── routes/                  # API routes
│   │   ├── __init__.py
│   │   ├── payroll.py           # POST /calculate and GET /payslip
│
│   ├── database/                # DB setup
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLAlchemy session, Base, engine
│
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Environment loader (dotenv)
│   │   ├── country_config.json  # Your updated config JSON
│
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py          # API Key verification
│
├── tests/
│   ├── __init__.py
│   ├── test_payroll_calculations.py  # Unit tests for services
│   ├── test_api.py                    # API integration tests
│
├── payslips/                  # Generated payslip PDFs
│
├── README.md                  # Setup and run instructions
├── requirements.txt           # Python dependencies (FastAPI, SQLAlchemy, WeasyPrint, etc.)
├── .env                       # Environment variables (DB URL, API KEYS)
├── run.sh                     # Optional: script to run uvicorn easily

Folder              | Purpose
app/models/         | All pydantic schemas (Employee, Allowances, etc.) and ORM models
app/services/       | Core calculation logic (gross pay, deductions, benefits, payslip generator)
app/routes/         | FastAPI route handlers (what /calculate does)
app/database/       | Connection setup with SQLAlchemy (Postgres, SQLite, etc.)
app/config/         | Environment configs and country payroll configs
app/utils/          | Security functions like API Key verification
tests/              | Unit and API tests
payslips/           | Folder to save the generated PDF files
.env                | Your secrets: database URL, API keys
requirements.txt    | Python packages (FastAPI, SQLAlchemy, etc.)


Steps to run the prototype app

1. Start the api listern service 

 uvicorn app.main:app --reload

2. open 2nd terminal and run the test scripts

pytest tests/test_bundle.py   