def calculate_country_specific_benefits(gross_pay: float, config: dict):
    employee_deductions = {}
    employer_contributions = {}

    for benefit in config.get("country_specific_benefits", []):
        name = benefit["name"]
        if "employee_rate" in benefit:
            employee_deductions[name] = gross_pay * benefit["employee_rate"]
        if "employer_rate" in benefit:
            employer_contributions[name] = gross_pay * benefit["employer_rate"]

    total_employee = sum(employee_deductions.values())
    total_employer = sum(employer_contributions.values())

    return {
        "employee_total": round(total_employee, 2),
        "employer_total": round(total_employer, 2),
        "employee_breakdown": {k: round(v, 2) for k, v in employee_deductions.items()},
        "employer_breakdown": {k: round(v, 2) for k, v in employer_contributions.items()}
    }