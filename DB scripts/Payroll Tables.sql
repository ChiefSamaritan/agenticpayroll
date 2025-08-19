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
    tenant_id INT REFERENCES tenant(id)
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
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
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

-- Data rows:
INSERT INTO tenant (id, name, address ) VALUES ('12', 'Bolivia Tenant', 'Avenida Busch 1456  
Edificio Torres Mall, Piso 5  
Santa Cruz de la Sierra, Bolivia');

INSERT INTO employee (id, full_name, job_title, department, country, tax_id, bank_account_last4)
VALUES (
    'emp-bo-001',
    'Lucía Quispe',
    'Finance Analyst',
    'Accounting',
    'Bolivia',
    'BO654321987',
    '9988'
);

select * from tenant