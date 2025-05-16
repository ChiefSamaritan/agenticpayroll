import uuid
from app.services.payslip import generate_payslip
from app.models.employee import Employee, CompanyMetadata

# Dummy data setup
employee = Employee(
    tenant_id="test-tenant",
    employee_id="emp-001",
    country="USA",
    gross_salary=80000,
    hourly_rate=40,
    hours_worked=160,
    overtime_hours=10,
    bonuses=2000,
    allowances={"meal_allowance": 300, "remote_work_allowance": 150},
    benefits_opt_in={},
    metadata={
        "full_name": "Jane Doe",
        "job_title": "Engineer",
        "department": "Engineering",
        "tax_id": "US000000",
        "bank_account_last4": "1234"
    }
)

company = CompanyMetadata(
    company_name="TestCorp Inc.",
    address="123 Test Street, Test City, USA"
)

breakdown = {
    "base_pay": 6400.00,
    "overtime_pay": 500.00,
    "allowances_breakdown": {
        "meal_allowance": 300,
        "remote_work_allowance": 150
    },
    "gross_pay": 9350.00,
    "net_pay": 7800.00,
    "income_tax": 800,
    "social_security": 310,
    "health_insurance": 100,
    "solidarity_fund": 0,
    "total_deductions": 1550,
    "employer_costs": {
        "social_security_employer": 310,
        "health_insurance_employer": 100
    }
}

employer_cost = {
    "total_employer_cost": 410
}

# Test function
if __name__ == "__main__":
    path = generate_payslip(employee, breakdown, breakdown["net_pay"], employer_cost, company)
    print(f"\n✅ Payslip generated at: {path}")