from app.models.employee import Employee

def calculate_gross_pay(employee: Employee, config: dict):
    base_pay = employee.hourly_rate * employee.hours_worked
    overtime_pay = employee.overtime_hours * (employee.hourly_rate * 1.25)
    total_allowances = 0.0
    applicable_allowances = {}

    if employee.allowances:
        for allowance_name, allowance_amount in employee.allowances.items():
            if allowance_amount > 0:
                applicable_allowances[allowance_name] = allowance_amount
                total_allowances += allowance_amount

    gross_pay = base_pay + overtime_pay + employee.bonuses + total_allowances
    return gross_pay, base_pay, overtime_pay, applicable_allowances

def calculate_taxable_gross(gross: float, config: dict, employee: Employee):
    exemptions = config.get("tax_exemptions", {})
    deduction_total = 0.0

    if not exemptions:
        return gross, 0.0

    for name, rule in exemptions.items():
        # If the employee opted in (or exemption is always applied)
        opted_in = True
        if employee.benefits_opt_in:
            opted_in = getattr(employee.benefits_opt_in, name, True)

        if opted_in:
            if rule["type"] == "fixed":
                deduction_total += rule["amount"]
            elif rule["type"] == "percentage":
                deduction_total += gross * rule["rate"]

    return max(gross - deduction_total, 0), deduction_total