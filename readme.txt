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