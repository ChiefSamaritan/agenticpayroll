from pydantic import BaseModel
from typing import Optional, Dict

class CompanyMetadata(BaseModel):
    company_name: str
    address: Optional[str] = None
    logo_url: Optional[str] = None

class EmployeeMetadata(BaseModel):
    full_name: str
    job_title: Optional[str] = None
    department: Optional[str] = None
    tax_id: Optional[str] = None
    bank_account_last4: Optional[str] = None

class BenefitsOptIn(BaseModel):
    private_pension: Optional[bool] = False
    health_insurance_top_up: Optional[bool] = False
    meal_subsidy: Optional[bool] = False

class Employee(BaseModel):
    tenant_id: str
    employee_id: str
    country: str
    gross_salary: float
    hourly_rate: float
    hours_worked: float
    overtime_hours: Optional[float] = 0.0
    bonuses: Optional[float] = 0.0
    allowances: Optional[Dict[str, float]] = {}
    benefits_opt_in: Optional[BenefitsOptIn] = BenefitsOptIn()
    metadata: Optional[EmployeeMetadata] = None

class PayrollRequest(BaseModel):
    employee: Employee
    company: Optional[CompanyMetadata] = None