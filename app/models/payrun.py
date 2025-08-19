# app/models/payrun.py
from sqlalchemy import (
    Column, Integer, String, Text, Date, Numeric, TIMESTAMP, ForeignKey, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# --- Reference table so FKs can resolve ---
class Tenant(Base):
    __tablename__ = "tenant"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(Text)

class Payrun(Base):
    __tablename__ = "payrun"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"))
    country = Column(String(50), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    run_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    status = Column(String(20), nullable=False)  # 'draft','approved','posted'
    description = Column(Text)
    total_gross = Column(Numeric(12, 2))
    total_net = Column(Numeric(12, 2))
    total_tax = Column(Numeric(12, 2))
    total_employer_cost = Column(Numeric(12, 2))

class Employee(Base):
    __tablename__ = "employee"
    id = Column(String(50), primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"))
    full_name = Column(Text, nullable=False)
    email = Column(Text)
    job_title = Column(Text)
    department = Column(Text)
    country = Column(String(50), nullable=False)
    tax_id = Column(String(50))
    bank_account_last4 = Column(String(10))
    hire_date = Column(Date)
    base_pay = Column(Numeric(12, 2))
    hourly_rate = Column(Numeric(12, 2))
    termination_date = Column(Date)
    status = Column(String(20), default="active")
    date_of_birth = Column(Date)

class EmployeePay(Base):
    __tablename__ = "employee_pay"
    id = Column(Integer, primary_key=True)
    payrun_id = Column(Integer, ForeignKey("payrun.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(50), ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id"))
    country = Column(String(100))
    pay_period = Column(String(50))
    pay_type = Column(String(20))  # Monthly, Bi-weekly
    base_pay = Column(Numeric(12, 2))
    overtime_pay = Column(Numeric(12, 2))
    bonuses = Column(Numeric(12, 2))
    hours_worked = Column(Numeric(8, 2))
    overtime_hours = Column(Numeric(8, 2))
    gross_pay = Column(Numeric(12, 2))
    taxable_income = Column(Numeric(12, 2))
    income_tax = Column(Numeric(12, 2))
    social_security = Column(Numeric(12, 2))
    health_insurance = Column(Numeric(12, 2))
    solidarity_fund = Column(Numeric(12, 2))
    total_deductions = Column(Numeric(12, 2))
    net_pay = Column(Numeric(12, 2))
    total_employer_cost = Column(Numeric(12, 2))
    total_pre_tax = Column(Numeric(12, 2))
    total_post_tax = Column(Numeric(12, 2))
    tax_bracket_details = Column(JSONB)
    tax_exemptions_applied = Column(JSONB)
    country_specific_benefits = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    issued_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class EmployeeAllowances(Base):
    __tablename__ = "employee_allowances"
    id = Column(Integer, primary_key=True)
    payslip_id = Column(Integer, ForeignKey("employee_pay.id", ondelete="CASCADE"))
    name = Column(String(100))
    amount = Column(Numeric(12, 2))
    pre_tax = Column(Boolean, default=False)
    tax_exempt = Column(Boolean, default=False)

class EmployerContributions(Base):
    __tablename__ = "employer_contributions"
    id = Column(Integer, primary_key=True)
    payslip_id = Column(Integer, ForeignKey("employee_pay.id", ondelete="CASCADE"))
    contribution_type = Column(String(100))
    amount = Column(Numeric(12, 2))

class EmployeeBenefitsDeductions(Base):
    __tablename__ = "employee_benefits_deductions"
    id = Column(Integer, primary_key=True)
    payslip_id = Column(Integer, ForeignKey("employee_pay.id", ondelete="CASCADE"))
    deduction_type = Column(String(100))  # pre_tax / post_tax
    benefit_name = Column(String(100))
    amount = Column(Numeric(12, 2))
    payer = Column(String(20))  # 'employee' or 'employer'